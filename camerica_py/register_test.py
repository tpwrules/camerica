import os
import mmap

# where the camerica regs are in the HPS memory space
LWFPGASLAVES = 0xFF200000
CAMERICA_REG_BASE = LWFPGASLAVES+0x32000

# set up a memory mapping of the camerica regs
print("Mapping camerica registers...")
mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
regs = mmap.mmap(mem_fd, 16, offset=CAMERICA_REG_BASE)

# test them out by reading and writing the DMA address
print("Current DMA register value: 0x{:02x}".format(regs[0]))
print("Writing its inverse...")
regs[0] = regs[0] ^ 0xFF
print("New DMA register value: 0x{:02x}".format(regs[0]))

os.close(mem_fd)