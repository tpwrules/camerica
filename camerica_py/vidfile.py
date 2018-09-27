# classes for reading and writing video files

import struct
import os
import threading
import queue

import numpy as np
import random

class VidfileWriter:
    def __init__(self, path, width, height, fps):
        self.path = path
        self.width = width
        self.height = height
        self.fps = fps
        self.pack_type = 0 # uncompressed
        # random id so that files probably won't get crosslinked
        self.file_id = random.randint(0, 2**64-1)
        
        self.is_open = True
        
        self.vf_curr_file_num = 0
        self.vf_start()
        
        # open index file
        self.index_file = open(self.path+".idx", "wb")
        # and save the file ID to it
        self.index_file.write(struct.pack("<Q", self.file_id))
        
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
                (self.fps, 257), dtype=np.uint32)
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
        hbuf[fi, :256] = histo
        hbuf[fi, 256] = frame_num
        
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
        
        # sync and close the index and video data files
        self.index_file.flush()
        os.fsync(self.index_file.fileno())
        self.index_file.close()
        
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
            
            # save the current position in the file
            # so that we can add it to the index
            buf_pos = self.vf_curr_file.tell()
            
            # write the file data out
            self.vf_curr_file.write(struct.pack("<I", nbuf))
            self.vf_curr_file.write(fbuf.data)
            self.vf_curr_file.write(hbuf.data)
            
            # put the buffer on the empty queue now that we're done
            self.vf_written_bufs.put((fbuf, hbuf))
            
            self.vf_curr_file.flush()
            
            # update the index file too
            self.index_file.write(struct.pack("<II", 
                self.vf_curr_file_num, buf_pos))
            self.index_file.flush()
            
            # start a new file if we've gone over this one's size
            if self.vf_curr_file.tell() > 3*1024*1024*1024:
                # force current one to be saved to disk
                os.fsync(self.vf_curr_file.fileno())
                self.vf_curr_file.close()
                # force flush of index file too
                os.fsync(self.index_file.fileno())
                
                # open a new file with a new name
                self.vf_curr_file_num += 1
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
            self.pack_type,
            self.vf_curr_file_num))


class VidfileReader:
    def __init__(self, path, initial_frame=0):
        self.path = path
        
        self.is_open = True
        
        # open the first vidfile so we can extract its metadata
        self.vf_curr_file = open(self.path, "rb")
        meta = struct.unpack("<Q5I", self.vf_curr_file.read(8+5*4))
        self.file_id = meta[0]
        self.width = meta[1]
        self.height = meta[2]
        self.fps = meta[3]
        self.pack_type = meta[4]
        self.vf_curr_file_num = meta[5]
        if self.vf_curr_file_num != 0:
            raise ValueError("first vidfile should be numbered 0")
            
        # attempt to open and read the index
        self.seek_disabled_reason = None
        try:
            indexf = open(self.path+".idx", "rb")
            index_id, = struct.unpack("<Q", indexf.read(8))
            if index_id != self.file_id:
                raise ValueError("index is not for this vidfile")
            self.seek_table = []
            while True:
                record = indexf.read(8)
                if len(record) == 0:
                    break
                if len(record) != 8:
                    raise ValueError("index is not complete")
                self.seek_table.append(struct.unpack("<II", record))
        except Exception as e:
            self.seek_disabled_reason = str(e)
            
        # create queues and events for reader thread
        self.vf_bufs_to_read = queue.Queue()
        self.vf_read_bufs = queue.Queue()
        self.should_be_reading = threading.Event()
        self.stopped_reading = threading.Event()
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
                (self.fps, 257), dtype=np.uint32)
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
        # get a new buffer, if necessary
        if self.vf_curr_buf is None:
            self.vf_curr_buf_frames, self.vf_curr_buf = \
                self.vf_read_bufs.get()
            self.vf_curr_bufi = 0
        
        # copy from the buffer into the user's
        fbuf, hbuf = self.vf_curr_buf
        np.copyto(frame, fbuf[self.vf_curr_bufi, :, :])
        np.copyto(histo, hbuf[self.vf_curr_bufi, :256])
        frame_num = hbuf[self.vf_curr_bufi, 256]
        self.vf_curr_bufi += 1
        self.vf_curr_frame += 1
        
        # queue the buffer for refilling if we've emptied it
        if self.vf_curr_bufi == self.vf_curr_buf_frames:
            self.vf_bufs_to_read.put(self.vf_curr_buf)
            self.vf_curr_buf = None
            
        # and return which frame was just read (counting dropped frames)
        return frame_num
        
    def seek(self, frame):
        if not self.is_open:
            raise ValueError("attempted to seek on closed Vidfile")
        if frame == 0:
            # just rewind back to the beginning
            self.should_be_reading.clear()
            #self.vf_bufs_to_read.join()
            
            # all the bufs need refilling
            try:
                while True:
                    self.vf_bufs_to_read.put(
                        self.vf_read_bufs.get(block=False))
            except queue.Empty:
                pass
                
            # and we need to reopen the file
            self.vf_curr_file.close()
            self.vf_open(0)
            
            # and let the video reader get back to work
            self.should_be_reading.set()
            # read one buffer to make sure playback won't immediately lag
            self.vf_curr_buf_frames, self.vf_curr_buf = \
                self.vf_read_bufs.get()
            self.vf_curr_bufi = 0
            self.vf_curr_frame = 0
            
            return
            
        # otherwise, make sure we can actually seek
        if self.seek_disabled_reason is not None:
            raise ValueError("Cannot seek: "+self.seek_disabled_reason)
            
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
        # tell the frame reader to stop as all its work is in vain
        self.should_be_reading.clear()
        self.vf_bufs_to_read.join()
        
        # all the bufs need refilling
        try:
            while True:
                self.vf_bufs_to_read.put(
                    self.vf_read_bufs.get(block=False))
        except queue.Empty:
            pass
            
        # open the correct file
        fn, fpos = self.seek_table[frame//self.fps]
        if fn != self.vf_curr_file_num:
            self.vf_curr_file.close()
            self.vf_open(fn)
        self.vf_curr_file.seek(fpos)
        
        # and let the video reader get back to work
        self.should_be_reading.set()
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
        self.should_be_reading.set()
        self.vf_reader_thread.join()
        
        # delete our buffers to free up memory
        self.vf_curr_file.close()
        del self.vf_curr_file
        del self.vf_bufs_to_read
        del self.vf_read_bufs
        
    def start_vf_reader(self):
        try:
            self.vf_reader()
        except Exception as e:
            self.vf_exception = e
            
    def vf_reader(self):
        while True:
            # make sure we're allowed to read
            self.should_be_reading.wait()
            
            bufs = self.vf_bufs_to_read.get()
            if bufs == None: # asked kindly to exit
                break
            fbuf, hbuf = bufs
            
            nbufbytes = self.vf_curr_file.read(4)
            if len(nbufbytes) == 0: # must have hit EOF
                self.vf_curr_file_num += 1
                self.vf_open(self.vf_curr_file_num)
                nbufbytes = self.vf_curr_file.read(4)
            
            nbuf, = struct.unpack("<I", nbufbytes)
            self.vf_curr_file.readinto(fbuf.data)
            self.vf_curr_file.readinto(hbuf.data)
            
            self.vf_read_bufs.put((nbuf, (fbuf, hbuf)))
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
        self.vf_curr_file.seek(8+5*4)
        self.vf_curr_file_num = num
