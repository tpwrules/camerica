# this file manages the classes that abstract over
# the Camerica hardware

import struct
import os
import mmap
import numpy as np
from enum import IntEnum

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
        
def is_hardware_present():
    # first, check to see if we are running on the FPGA we expect
    # if we aren't, just don't use the hardware
    # the user will notice they can't plug the camera in
    # and conclude the camera shouldn't be working
    try:
        machine = open("/sys/devices/soc0/machine", "r").read()
    except:
        # we can't open it, so probably not
        return False
    if machine != "Terasic DE10 Standard\n":
        # it has the wrong machine, so most likely not
        return False
    
    # now, check to see if the hardware sysid exists where we
    # expect
    # if it doesn't, we can tell the user so maybe they
    # can fix the problem
    try:
        sysid = open("/sys/devices/platform/sopc@0/ff200000.bridge/"+
            "ff210000.sysid/sysid/id", "r").read()
    except:
        print("COULD NOT USE HARDWARE")
        print("FPGA detected but sysid was not found.")
        print("Is the FPGA running the correct configuration?")
        return False
        
    try:
        sysid = int(sysid)
    except:
        sysid = None
    if sysid != 0xACD93B30:
        print("COULD NOT USE HARDWARE")
        print("FPGA detected but sysid is incorrect.")
        print("Is the FPGA running the latest configuration?")
        return False
        
    # if the sysid exists and is correct, we must believe that the
    # hardware is present and working
    return True
    
# which camera the hardware should expect
# if NONE, all cameras are disconnected
class CameraType(IntEnum):
    NONE = 0
    MERLIN = 1
    PHOTON_640 = 2

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
        self.cam_type = CameraType.NONE # don't connect a camera
        
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
    def dma_active(self):
        return True if self.status & 2 else False
        
        
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
    def new_dma_phys(self):
        return True if self.status & 128 else False
    
    @new_dma_phys.setter
    def new_dma_phys(self, value):
        if value is not True:
            raise ValueError("new_dma_phys can only be set to True")
        self.control |= 128
            
    @property
    def cam_type(self):
        t = (self.control & 0xF00) >> 8
        try:
            return CameraType(t)
        except ValueError: # hardware may have a nonsense value
            return CameraType.NONE
            
    @cam_type.setter
    def cam_type(self, value):
        if not isinstance(value, CameraType):
            raise ValueError(
                "expected a CameraType, not {}".format(repr(value)))
        self.control = (self.control & 0xFFFFF0FF) | (value.value << 8)
            
class UDMABuf:
    def __init__(self, name, expected_size):
        self.name = name
        self.path = "/sys/class/udmabuf/{}/".format(name)
        self.mmap_path = "/dev/{}".format(name)
        
        # test to see if the device exists
        if not os.path.isdir(self.path):
            raise Exception("UDMA buffer {} does not exist".format(name))
            
        # and then to see if it's the correct size
        size = int(self._cat("size"))
        if size < expected_size:
            raise Exception(
                "UDMA buffer {} must be {} bytes (it's currently {})".format(
                expected_size, size))
        
        # now save the physical addr
        self.phys_addr = int(self._cat("phys_addr"), 16)
        
        # enable CPU cache
        self._echo("sync_mode", str(0))
        
        # set the entire dma region to be synchronized
        self._echo("sync_offset", str(0))
        self._echo("sync_size", str(size))
        
        # the device is the one writing to the buffer
        self._echo("sync_direction", str(2))
        
    def _cat(self, fn):
        path = os.path.join(self.path, fn)
        return open(path, "r").read()
        
    def _echo(self, fn, val):
        path = os.path.join(self.path, fn)
        f = open(path, "w")
        f.write(val)
        f.close()
        
    def flush_cache(self):
        # claim ownership of the buffer to force the
        # CPU cache to be discarded
        self._echo("sync_for_cpu", str(1))
            
            
class Framequeue:
    def __init__(self, regs, camera):
        self.regs = regs
        self.camera = camera
        
        # construct 32 frame and histo buffers
        self.udmabufs = []
        self.frames = []
        self.histos = []
        # stores pairs of (frame, histo) buffers that the above ones are copied to
        self.copybufs = []
        for bi in range(32):
            udmabuf = UDMABuf("udmabuf{}".format(bi),
                self.camera.width*self.camera.height*2)
            self.udmabufs.append(udmabuf)
            self.frames.append(np.memmap(udmabuf.mmap_path,
                dtype=np.uint16, mode='r',
                offset=0, shape=(self.camera.height, self.camera.width)))
            self.histos.append(np.memmap(udmabuf.mmap_path,
                dtype=np.uint32, mode='r',
                offset=self.camera.width*self.camera.height*2,
                shape=(512,)))
            
            self.copybufs.append((
                np.empty((self.camera.height, self.camera.width), dtype=np.uint16),
                np.empty((512,), dtype=np.uint32)
            ))
                
    def start(self):
        # make sure we're stopped
        self.stop()
        # set the correct type of camera to connect the receiver
        self.regs.cam_type = self.camera.hw_type
        # write the latest physical addrs to the hardware
        for ui, udmabuf in enumerate(self.udmabufs):
            # write this phys addr
            # (pack number into low byte)
            self.regs.dma_phys_addr = udmabuf.phys_addr | (ui & 0xFF)
            # tell the hardware it's new
            self.regs.new_dma_phys = True
            # wait til the hardware accepts it
            while self.regs.new_dma_phys: pass
        
        # write to buffer 0xFF to tell the hardware we're finished
        self.regs.dma_phys_addr = 0xFF
        self.regs.new_dma_phys = True
        while self.regs.new_dma_phys: pass
            
        # we start at frame 0 when DMA is enabled
        self.last_frame_counter = 0
        # kick off the DMA
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
        if new_frames > 31: # we missed some frames
            dropped_frames = new_frames - 31
            new_frames = 31
            
        # calculate buffer to start on
        which_buf = (frame_counter - new_frames) % 32
        
        result = []
        
        copyi = 0
        
        while new_frames:
            # invalidate CPU cache for this frame buffer area
            # so we get the most up to date copy
            self.udmabufs[which_buf].flush_cache()
            copybuf = self.copybufs[copyi]
            copyi += 1
            np.copyto(copybuf[0], self.frames[which_buf])
            np.copyto(copybuf[1], self.histos[which_buf])
            result.append(copybuf)
            which_buf = (which_buf + 1) % 32
            new_frames -= 1
        
        return result, dropped_frames