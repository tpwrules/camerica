# video handling logic for Studio

import numpy as np
import threading
import queue
import time
from enum import Enum

import camerica_hw as hw

class VidHandler:
    def __init__(self, width, height, fps, bufs):
        self.width = width
        self.height = height
        self.fps = fps
        self.framebuf, self.histobuf = bufs
        
        self.is_running = True
        
        # make a lock so that frames don't get half-read
        self.buf_lock = threading.Lock()
        
        # create command queue for the handler thread
        self.h_cmds = queue.Queue()
        
        # and any pending exception from the handler thread
        self.h_exception = None
        
        # and get it ready for action
        self.handler_thread = threading.Thread(
            target=self.start_handler)
        
    def lock_frame(self):
        if not self.is_running:
            raise ValueError("vid handler stopped")
        self.buf_lock.acquire()
        
    def unlock_frame(self):
        if not self.is_running:
            raise ValueError("vid handler stopped")
        self.buf_lock.release()
        
    def stop(self):
        if not self.is_running:
            return
        self.h_cmds.put(("terminate",))
        self.handler_thread.join()
        self.fq.stop()
        self.is_running = False
        if self.h_exception is not None:
            raise self.h_exception
            
    def __del__(self):
        try:
            self.stop()
        except:
            pass
        
    
    def start_handler(self):
        try:
            self.handler()
        except Exception as e:
            self.h_exception = e
            
    
        

# live display of the video, without any recording or playback
class VidLiveHandler(VidHandler):
    def __init__(self, width, height, fps, bufs):
        # check that the hardware exists
        if not hw.is_hardware_present():
            raise ValueError("hardware missing")
            
        super().__init__(width, height, fps, bufs)
        
        # instantiate the hardware and video buffer
        self.hw_regs = hw.Registers()
        self.udmabuf = hw.UDMABuf("udmabuf0")
        # and the framebuffer attached to the hardware
        self.fq = hw.Framequeue(self.udmabuf, self.hw_regs)
        
        # save also the current frame progress
        self.total_frames = 0
        self.dropped_frames = 0
        
        # now start up the handler thread
        self.handler_thread.start()
        
    
    def handler(self):
        # start capturing frames
        self.fq.start()
        terminated = False
        while not terminated:
            # process any commands
            try:
                while not self.h_cmds.empty():
                    cmd = self.h_cmds.get(block=False)
                    if cmd[0] == "terminate":
                        terminated = True
                        break
            except queue.Empty:
                pass
                
            # and any frames from hardware
            frame_data, just_dropped = self.fq.get_new_frames()
            if len(frame_data) > 0:
                with self.buf_lock:
                    self.dropped_frames += just_dropped
                    self.total_frames += len(frame_data)
                    np.copyto(self.framebuf, frame_data[-1][0])
                    np.copyto(self.histobuf, frame_data[-1][1])
            
            time.sleep(0.03) # avoid banging hardware
                