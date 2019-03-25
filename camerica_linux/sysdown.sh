#!/bin/bash

# find camerica directory
cd /root/camerica/repo/camerica_py

echo "UNMOUNTING RECORDINGS DIRECTORY"
umount /root/recordings


echo "DISABLING CAMERICA HARDWARE"
source /root/camerica/venv/bin/activate
printf 'from camerica_hw import Registers; regs = Registers(); regs.dma_enabled = False; \nwhile regs.dma_active: pass' | python3


# unload the udmabuf
rmmod udmabuf
