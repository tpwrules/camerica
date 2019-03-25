#!/bin/bash

# find camerica directory
cd /root/camerica/repo/camerica_py

echo "UNMOUNTING RECORDINGS DIRECTORY"
umount /root/recordings


echo "DISABLING CAMERICA HARDWARE"
source /root/camerica/venv/bin/activate
cat << DISPY | python3
import contextlib
import camerica_hw
with contextlib.redirect_stdout(None):
    if camerica_hw.detect_hardware():
        regs = camerica_hw.Registers()
        regs.dma_enabled = False
        while regs.dma_active:
            pass
DISPY


# unload the udmabuf if it's currently loaded
echo "DEALLOCATING DMA BUFFERS"
lsmod | grep udmabuf > /dev/null
if [ $? -eq 0 ]; then
    rmmod udmabuf
fi

echo "SYSTEM SHUTDOWN COMPLETE"
