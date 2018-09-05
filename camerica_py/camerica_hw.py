# this file manages the classes that abstract over
# the Camerica hardware

import struct
import os
import mmap

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