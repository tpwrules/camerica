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
            self.index_file.write(struct.pack("<3I", 
                self.vf_curr_file_num, buf_pos, nbuf))
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
 