#!/bin/bash

# find camerica directory
cd /root/camerica/repo/camerica_py

# stop camera engine
source /root/camerica/venv/bin/activate
printf 'from camerica_hw import Registers; regs = Registers(); regs.dma_enabled = False; \nwhile regs.dma_active: pass' | python3


# unload the udmabuf
rmmod udmabuf
