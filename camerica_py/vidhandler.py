# video handling logic for Studio

import numpy as np
import threading
import queue
import time
from enum import Enum

import camerica_hw as hw
import vidfile

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
        # stop ourselves if the handler thread died
        if self.h_exception is not None:
            self.stop() # (stopping will raise the exception)
        self.buf_lock.acquire()
        
    def unlock_frame(self):
        if not self.is_running:
            raise ValueError("vid handler stopped")
        self.buf_lock.release()
        # stop ourselves if the handler thread died
        if self.h_exception is not None:
            self.stop() # (stopping will raise the exception)
        
    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self.h_cmds.put(("terminate",))
        self.handler_thread.join()
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
        self.current_frame = 0
        self.dropped_frames = 0
        self.saved_frames = 0
        
        # now start up the handler thread
        self.handler_thread.start()
        
    def stop(self):
        try:
            super().stop()
        finally:
            self.fq.stop()
    
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
                    self.saved_frames += len(frame_data)
                    self.current_frame += (just_dropped+len(frame_data))
                    np.copyto(self.framebuf, frame_data[-1][0])
                    np.copyto(self.histobuf, frame_data[-1][1])
            
            time.sleep(0.03) # avoid banging hardware
                

# live display of the video, without any recording or playback
class VidRecordHandler(VidHandler):
    def __init__(self, width, height, fps, bufs, fname):
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
        self.current_frame = 0
        self.dropped_frames = 0
        self.saved_frames = 0
        
        # and create a vidfile to save the recording in
        self.vf = vidfile.VidfileWriter(fname, width, height, fps)
        
        # now start up the handler thread
        self.handler_thread.start()
        
    def stop(self):
        if not self.is_running:
            return
        try:
            super().stop()
        finally:
            self.fq.stop()
            self.vf.close()
    
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
            self.dropped_frames += just_dropped
            self.current_frame += just_dropped
            if len(frame_data) > 0:
                for frame, histo in frame_data:
                    self.vf.write(self.current_frame, frame, histo)
                    self.current_frame += 1
                    self.saved_frames += 1
                with self.buf_lock:
                    np.copyto(self.framebuf, frame_data[-1][0])
                    np.copyto(self.histobuf, frame_data[-1][1])
            
            time.sleep(0.03) # avoid banging hardware
            
# only playback of video, no hardware
class VidPlaybackHandler(VidHandler):
    def __init__(self, width, height, fps, bufs, fname):
        super().__init__(width, height, fps, bufs)
        
        self.playing = False
        
        # create the vidfile that the recording comes from
        self.vf = vidfile.VidfileReader(fname)
        
        self.vid_frame = 0
        self.current_frame = 0
        self.dropped_frames = 0
        self.saved_frames = self.vf.saved_frames
        
        # now start up the handler thread
        self.handler_thread.start()
        
    def stop(self):
        if not self.is_running:
            return
        try:
            super().stop()
        finally:
            self.vf.close()
            
    def seek(self, pos):
        self.h_cmds.put(("seek", pos))
    
    def playpause(self):
        self.h_cmds.put(("playpause", ))
    
    def handler(self):
        terminated = False
        do_next_frame = False
        while not terminated:
            # process any commands
            try:
                while not self.h_cmds.empty() and not terminated:
                    cmd = self.h_cmds.get(block=False)
                    if cmd[0] == "terminate":
                        terminated = True
                    elif cmd[0] == "seek":
                        self.vf.seek(cmd[1])
                        do_next_frame = True
                    elif cmd[0] == "playpause":
                        self.playing = not self.playing
                        if self.vid_frame == self.saved_frames-1:
                            self.playing = False
                    self.h_cmds.task_done()
            except queue.Empty:
                pass
                
            if terminated:
                break
                
            # and read the latest frame
            if self.playing or do_next_frame:
                do_next_frame = False
                with self.buf_lock:
                    self.current_frame, self.vid_frame = self.vf.next_frame(
                        self.framebuf, self.histobuf)
                    self.dropped_frames = self.current_frame-self.vid_frame
                if self.vid_frame == self.saved_frames-1:
                    self.playing = False
            
            time.sleep(1/self.fps) # wait one frame time (needs to be fixed)