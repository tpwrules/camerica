# classes for reading and writing video files

import struct
import os
import threading
import queue

import numpy as np
import random

MAX_FILE_SIZE = 3*1024*1024*1024
HEADER_SIZE = 8 + 5*4

class VidfileWriter:
    def __init__(self, path, width, height, fps):
        self.path = path
        self.width = width
        self.height = height
        self.fps = fps
        # pixels * 2bytespp + (512 histo entries+1 dropped frame count)
        # * 4 bytes per * fps + 4 byte frames this second
        bytes_per_second = (width*self.height*2+513*4)*fps + 4
        self.seconds_per_file = \
            int((MAX_FILE_SIZE-HEADER_SIZE)/bytes_per_second)
        # random id so that files probably won't get crosslinked
        self.file_id = random.randint(0, 2**64-1)
        
        self.is_open = True
        
        self.vf_curr_file_num = 0
        self.vf_curr_file_seconds = 0
        self.vf_start()
        
        # create queues for writer thread
        self.vf_bufs_to_write = queue.Queue()
        self.vf_written_bufs = queue.Queue()
        self.vf_exception = None
        
        # allocate write buffers
        self.vf_curr_buf = None
        self.vf_curr_bufi = 0
        for x in range(10):
            # each buffer can hold 1 second of video
            frame_buf = np.empty(
                (self.fps, self.height, self.width), dtype=np.uint16)
            histo_buf = np.empty(
                (self.fps, 513), dtype=np.uint32)
            self.vf_written_bufs.put((frame_buf, histo_buf))
        
        # and start said thread up
        self.vf_writer_thread = threading.Thread(
            target=self.start_vf_writer)
        self.vf_writer_thread.start()
            
    def write(self, frame_num, frame, histo):
        # frame and histo are numpy arrays containing
        # the appropriate data
        
        if not self.is_open:
            raise ValueError("attempted to write to closed Vidfile")
        
        # close the file if the writer died for some reason
        if self.vf_exception is not None:
            self.close()
            # close should not return (it will raise the exception)
            # but just in case
            return
        
        # make sure we have a buffer to write to
        if self.vf_curr_buf is None:
            self.vf_curr_bufi = 0
            self.vf_curr_buf = self.vf_written_bufs.get()
        
        fbuf, hbuf = self.vf_curr_buf
        # get which frame in the buffer we should use
        fi = self.vf_curr_bufi
        
        fbuf[fi, :, :] = frame
        hbuf[fi, :512] = histo
        hbuf[fi, 512] = frame_num
        
        self.vf_curr_bufi += 1
        
        # write this buffer out if it's full
        if self.vf_curr_bufi == self.fps:
            self.vf_bufs_to_write.put((self.fps, fbuf, hbuf))
            self.vf_curr_buf = None
            
    def close(self):
        if self.is_open is False:
            return
        self.is_open = False
        
        # write any remaining frames
        if self.vf_curr_buf is not None:
            self.vf_bufs_to_write.put(
                (self.vf_curr_bufi, *self.vf_curr_buf))
            self.vf_curr_buf = None
            
        # push None to tell the writer to exit
        self.vf_bufs_to_write.put(None)
        
        # wait for the writer to exit
        self.vf_writer_thread.join()
        
        # sync and close the video data file
        if self.vf_curr_file is not None:
            self.vf_curr_file.flush()
            os.fsync(self.vf_curr_file.fileno())
            self.vf_curr_file.close()
        
        # free up our buffers
        del self.vf_curr_buf
        del self.vf_bufs_to_write
        del self.vf_written_bufs
        
        # raise any exception the writer thread had
        if self.vf_exception is not None:
            e = self.vf_exception
            del self.vf_exception
            raise e
        
        
    def start_vf_writer(self):
        try:
            self.vf_writer()
        except Exception as e:
            self.vf_exception = e
            
    def vf_writer(self):
        while True:
            # get a new buffer to write
            fbuf = self.vf_bufs_to_write.get()
            if fbuf is None: # asked to exit
                break
            nbuf, fbuf, hbuf = fbuf
            
            # write the file data out
            self.vf_curr_file.write(struct.pack("<I", nbuf))
            self.vf_curr_file.write(fbuf.data)
            self.vf_curr_file.write(hbuf.data)
            
            # put the buffer on the empty queue now that we're done
            self.vf_written_bufs.put((fbuf, hbuf))
            
            self.vf_curr_file.flush()
            self.vf_curr_file_seconds += 1
            
            # start a new file if we've gone over this one's size
            if self.vf_curr_file_seconds == self.seconds_per_file:
                # force current one to be saved to disk
                os.fsync(self.vf_curr_file.fileno())
                f = self.vf_curr_file
                self.vf_curr_file = None
                f.close()
                
                # open a new file with a new name
                self.vf_curr_file_num += 1
                self.vf_curr_file_seconds = 0
                self.vf_start()
                
    def vf_start(self):
        if self.vf_curr_file_num == 0:
            name = self.path
        else:
            name = self.path + ".{:04d}".format(self.vf_curr_file_num)
            
        # open video file and write metadata to it
        self.vf_curr_file = open(name, "wb")
        self.vf_curr_file.write(struct.pack("<Q5I",
            self.file_id,
            self.width,
            self.height,
            self.fps,
            self.seconds_per_file,
            self.vf_curr_file_num))


class VidfileReader:
    def __init__(self, path, initial_frame=0):
        self.path = path
        
        self.is_open = True
        
        # open the first vidfile so we can extract its metadata
        self.vf_curr_file = open(self.path, "rb")
        meta = struct.unpack("<Q5I", self.vf_curr_file.read(HEADER_SIZE))
        self.file_id = meta[0]
        self.width = meta[1]
        self.height = meta[2]
        self.fps = meta[3]
        self.seconds_per_file = meta[4]
        self.vf_curr_file_num = meta[5]
        if self.vf_curr_file_num != 0:
            raise ValueError("first vidfile should be numbered 0")
            
        bytes_per_second = (self.width*self.height*2+513*4)*self.fps + 4
            
        # now find all the other vidfiles and open them
        # so we can figure out how many frames the video is
        # (and also validate them)
        self.total_frames = 0
        self.vf_total_files = 0
        was_last_file = False
        for fnum in range(10000):
            if fnum == 0:
                name = self.path
            else:
                name = self.path + "{:04d}".format(fnum)
            try:
                f = open(name, "rb")
            except:
                break
            if was_last_file:
                raise ValueError("vidfile {} is unexpected".format(name))
            meta = struct.unpack("<Q5I", f.read(HEADER_SIZE))
            if meta[0] != self.file_id:
                raise ValueError("vidfile {} has incorrect ID".format(name))
            if meta[5] != fnum:
                raise ValueError("vidfile {} has incorrect number".format(name))
            seconds_in_file = int((os.path.getsize(name)-HEADER_SIZE)/bytes_per_second)
            if (os.path.getsize(name)-HEADER_SIZE)%bytes_per_second != 0:
                raise ValueError("vidfile {} is incomplete".format(name))
            self.vf_total_files += 1
            self.total_frames += (seconds_in_file - 1) * self.fps
            # last second might be incomplete
            f.seek(HEADER_SIZE+(seconds_in_file-1)*bytes_per_second)
            frames_in_second, = struct.unpack("<I", f.read(4))
            self.total_frames += frames_in_second
            if frames_in_second != self.fps:
                was_last_file = True # it has to be now
            f.close()
            
        # create queues and events for reader thread
        self.vf_bufs_to_read = queue.Queue()
        self.vf_read_bufs = queue.Queue()
        self.vf_exception = None
            
        # allocate read buffers
        self.vf_curr_buf = None
        self.vf_curr_bufi = 0
        self.vf_curr_buf_frames = 0
        self.vf_curr_frame = 0
        for x in range(10):
            # each buffer can hold 1 second of video
            frame_buf = np.empty(
                (self.fps, self.height, self.width), dtype=np.uint16)
            histo_buf = np.empty(
                (self.fps, 513), dtype=np.uint32)
            self.vf_bufs_to_read.put((frame_buf, histo_buf))
         
        # start reading in separate thread
        self.vf_reader_thread = threading.Thread(
            target=self.start_vf_reader)
        self.vf_reader_thread.start()
            
        # and seek to the frame the user requested
        self.seek(initial_frame)
        
    def next_frame(self, frame, histo):
        if not self.is_open:
            raise ValueError("attempted to read from closed Vidfile")
        if self.vf_curr_frame == self.total_frames:
            return None
            
        # get a new buffer, if necessary
        if self.vf_curr_buf is None:
            self.vf_curr_buf_frames, self.vf_curr_buf = \
                self.vf_read_bufs.get()
            self.vf_curr_bufi = 0
        
        # copy from the buffer into the user's
        fbuf, hbuf = self.vf_curr_buf
        np.copyto(frame, fbuf[self.vf_curr_bufi, :, :])
        np.copyto(histo, hbuf[self.vf_curr_bufi, :512])
        frame_num = hbuf[self.vf_curr_bufi, 512]
        self.vf_curr_bufi += 1
        self.vf_curr_frame += 1
        
        # queue the buffer for refilling if we've emptied it
        if self.vf_curr_bufi == self.vf_curr_buf_frames:
            self.vf_bufs_to_read.put(self.vf_curr_buf)
            self.vf_curr_buf = None
            
        # and return which frame was just read (counting dropped frames)
        return frame_num
        
    def seek(self, frame):
        # do we actually need to seek?
        if frame == self.vf_curr_frame: return
        
        delta = frame-self.vf_curr_frame
        
        # can we seek within the current buffer?
        if delta+self.vf_curr_bufi < self.vf_curr_buf_frames and \
                delta+self.vf_curr_bufi >= 0:
            self.vf_curr_bufi += delta
            self.vf_curr_frame += delta
            return
            
        # ah well, discard what we have
        # get all the buffers waiting to be read
        bufs = []
        try:
            while True:
                bufs.append(self.vf_bufs_to_read.get(block=False))
                self.vf_bufs_to_read.task_done()
        except queue.Empty:
            pass
        # wait for any we didn't catch to be processed
        self.vf_bufs_to_read.join()
        # pull out the bufs that have been read also
        try:
            while True:
                bufs.append(self.vf_read_bufs.get(block=False)[1])
        except queue.Empty:
            pass
        # don't forget the buf currently being worked on!!!
        if self.vf_curr_buf is not None:
            bufs.append(self.vf_curr_buf)
            self.vf_curr_buf = None
            
        # open the correct file
        bytes_per_second = (self.width*self.height*2+513*4)*self.fps + 4
        sec = int(frame/self.fps)
        fnum = int(sec/self.seconds_per_file)
        if fnum != self.vf_curr_file_num:
            if self.vf_curr_file is not None:
                self.vf_curr_file.close()
            self.vf_open(fnum)
        self.vf_curr_file.seek(HEADER_SIZE+
            (sec-(fnum*self.seconds_per_file))*bytes_per_second)
        
        # now put the buffers back so the video reader does its job
        for buf in bufs:
            self.vf_bufs_to_read.put(buf)
        # read one buffer to make sure playback won't immediately lag
        self.vf_curr_buf_frames, self.vf_curr_buf = \
            self.vf_read_bufs.get()
        self.vf_curr_bufi = frame % self.fps
        self.vf_curr_frame = frame
        
    def close(self):
        if self.is_open is False:
            return
        self.is_open = False
        self.vf_bufs_to_read.put(None) # tell thread to exit
        self.vf_reader_thread.join()
        
        # delete our buffers to free up memory
        if self.vf_curr_file is not None:
            self.vf_curr_file.close()
        del self.vf_curr_file
        del self.vf_bufs_to_read
        del self.vf_read_bufs
        
    def start_vf_reader(self):
        self.vf_reader()
            
    def vf_reader(self):
        while True:
            bufs = self.vf_bufs_to_read.get()
            if bufs is None: # asked kindly to exit
                self.vf_bufs_to_read.task_done()
                break

            if self.vf_curr_file is None:
                if self.vf_curr_file_num == self.vf_total_files:
                    # we are finished reading the vidfile
                    # so fake read this buffer
                    self.vf_read_bufs.put((None, bufs))
                    self.vf_bufs_to_read.task_done()
                    continue # and wait for something else
                # open up the next vidfile
                self.vf_open(self.vf_curr_file_num)

            fbuf, hbuf = bufs
            
            nbufbytes = self.vf_curr_file.read(4)
            if len(nbufbytes) == 0:
                # hit the end of this file
                self.vf_curr_file.close()
                self.vf_curr_file = None
                self.vf_curr_file_num += 1
                # we can't actually finish this buffer
                # until the next loop, so put it back in the queue
                self.vf_bufs_to_read.put(bufs)
                self.vf_bufs_to_read.task_done()
                continue
                
            nbuf, = struct.unpack("<I", nbufbytes)
            self.vf_curr_file.readinto(fbuf.data)
            self.vf_curr_file.readinto(hbuf.data)
            
            self.vf_read_bufs.put((nbuf, bufs))
            self.vf_bufs_to_read.task_done()
                        
    def vf_open(self, num):
        if num == 0:
            name = self.path
        else:
            name = self.path + ".{:04d}".format(num)
            
        # open video file and read metadata from it
        self.vf_curr_file = open(name, "rb")
        new_file_id, = struct.unpack("<Q", self.vf_curr_file.read(8))
        if new_file_id != self.file_id:
            raise ValueError("vidfile {} has incorrect ID".format(name))
        self.vf_curr_file.seek(HEADER_SIZE)
        self.vf_curr_file_num = num
