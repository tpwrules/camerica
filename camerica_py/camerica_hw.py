# this file manages the classes that abstract over
# the Camerica hardware

import struct
import os
import mmap
import numpy as np

# where the camerica regs are in HPS memory space
# they're attached to the lightweight FPGA bus
LWFPGASLAVES = 0xFF200000
CAMERICA_REG_BASE = LWFPGASLAVES+0x32000
# make sure we can actually map at this offset
# since basically everything has a 4096 byte page size,
# it should always be possible, but who knows!
if CAMERICA_REG_BASE % mmap.ALLOCATIONGRANULARITY != 0:
    raise Exception(("CAMERICA_REG_BASE (0x{:08X}) doesn't line "+
        "up with ALLOCATIONGRANULARITY ({}). This shouldn't happen!").format(
        CAMERICA_REG_BASE, mmap.ALLOCATIONGRANULARITY))

# map the camerica hardware registers, then
# provide a way to access them easily
class Registers:
    def __init__(self):
        # open the file with physical memory
        # as read/write so we can touch the registers
        # and SYNC so cache doesn't get in the way
        self._mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        # create a mapping of the registers, there are 4x32bit ones
        self._regs = mmap.mmap(self._mem_fd, 16, offset=CAMERICA_REG_BASE)
        
        # set some important default values
        self.dma_enabled = False # don't stomp over random memory
        self.frame_ready = False # don't assume frame is there
        self.irq_enabled = False # don't interrupt until we're ready
        
    def __del__(self):
        # be nice and clean up our file descriptor
        try:
            os.close(self._mem_fd)
        except:
            # oh well
            pass
        
    @property
    def dma_phys_addr(self):
        return int.from_bytes(self._regs[:4], byteorder='little')
        
    @dma_phys_addr.setter
    def dma_phys_addr(self, value):
        self._regs[:4] = (value& 0xFFFFFFFF).to_bytes(4, byteorder='little')
    
        
    @property
    def frame_counter(self):
        return int.from_bytes(self._regs[4:8], byteorder='little')
    
        
    @property
    def status(self):
        return int.from_bytes(self._regs[8:12], byteorder='little')
    
    @property
    def cam_active(self):
        return True if self.status & 1 else False
    
    @property
    def dma_active(self):
        return True if self.status & 2 else False
    
    @property
    def frame_ready(self):
        return True if self.status & 4 else False
        
        
    @property
    def control(self):
        return int.from_bytes(self._regs[12:16], byteorder='little')
    
    @control.setter
    def control(self, value):
        self._regs[12:16] = (value & 0xFFFFFFFF).to_bytes(4, byteorder='little')
        
    @property
    def dma_enabled(self):
        return True if self.control & 2 else False
        
    @dma_enabled.setter
    def dma_enabled(self, value):
        if value:
            self.control |= 2
        else:
            self.control &= ~2
            
    @frame_ready.setter
    def frame_ready(self, value):
        # whatever the value, write 1 to clear the
        # frame ready status bit
        self.control |= 4
        
    @property
    def test_pattern(self):
        return True if self.control & 8 else False
    
    @test_pattern.setter
    def test_pattern(self, value):
        if value:
            self.control |= 8
        else:
            self.control &= ~8
            
    @property
    def irq_enabled(self):
        return True if self.control & 16 else False
    
    @irq_enabled.setter
    def irq_enabled(self, value):
        if value:
            self.control |= 16
        else:
            self.control &= ~16
            
            
class UDMABuf:
    def __init__(self, name):
        self.name = name
        self.path = "/sys/class/udmabuf/{}/".format(name)
        self.mmap_path = "/dev/{}".format(name)
        
        # test to see if the device exists
        if not os.path.isdir(self.path):
            raise Exception("UDMA buffer {} does not exist".format(name))
            
        # and then to see if it's the correct size
        size = int(self._cat("size"))
        if size < 4*1024*1024:
            raise Exception(
                "UDMA buffer {} must be {} bytes (it's currently {})".format(
                4*1024*1024, size))
        
        # now save the physical addr
        self.phys_addr = int(self._cat("phys_addr"), 16)
        
        # enable CPU cache
        self._echo("sync_mode", str(0))
        
        # set the entire dma region to be synchronized
        self._echo("sync_offset", str(0))
        self._echo("sync_size", str(4*1024*1024))
        # the device is the one writing to the buffer
        self._echo("sync_direction", str(2))
        
    def _cat(self, fn):
        path = os.path.join(self.path, fn)
        return open(path, "r").read()
        
    def _echo(self, fn, val):
        path = os.path.join(self.path, fn)
        f = open(path, "w")
        f.write(val)
        
    def flush_cache(self):
        # claim ownership of the buffer to force the
        # CPU cache to be cleared
        self._echo("sync_for_cpu", str(1))
            
            
class Framequeue:
    def __init__(self, udmabuf, regs):
        self.regs = regs
        self.udmabuf = udmabuf
        
        # construct 16 frame and histo buffers
        self.frames = []
        self.histos = []
        for bi in range(16):
            self.frames.append(np.memmap(udmabuf.mmap_path,
                dtype=np.uint16, mode='r',
                offset=256*1024*bi, shape=(256, 320)))
            self.histos.append(np.memmap(udmabuf.mmap_path,
                dtype=np.uint32, mode='r',
                offset=(256*1024*bi)+(320*256*2), shape=(256,)))
                
    def start(self):
        # make sure we're stopped
        #self.stop()
        # write the latest physical addr to the hardware
        self.regs.dma_phys_addr = self.udmabuf.phys_addr
        # save the current frame number so we can tell
        # if new frames have arrived
        self.last_frame_counter = self.regs.frame_counter
        # and kick off the DMA
        self.regs.dma_enabled = True
        
    def stop(self):
        # turn off DMA enable bit
        self.regs.dma_enabled = False
        # and wait until the engine finishes for real
        while self.regs.dma_active: pass
        
    def get_new_frames(self):
        # check if there are, in fact, any new frames
        frame_counter = self.regs.frame_counter
        new_frames = (frame_counter - self.last_frame_counter) & 0xFFFFFFFF
        self.last_frame_counter = frame_counter
    
        if new_frames == 0:
            return tuple(), 0
            
        dropped_frames = 0
        if new_frames > 15: # we missed some frames
            dropped_frames = new_frames - 15
            new_frames = 15
            
        # calculate buffer to start on
        which_buf = (frame_counter - new_frames) % 16
        
        result = []
        
        # invalidate CPU cache for the frame buffer area
        # so we get the most up to date copy
        self.udmabuf.flush_cache()
        
        while new_frames:
            frame = self.frames[which_buf].copy()
            histo = self.histos[which_buf].copy()
            result.append((frame, histo))
            which_buf = (which_buf + 1) % 16
            new_frames -= 1
        
        return result, dropped_frames