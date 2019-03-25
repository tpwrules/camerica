#!/bin/bash

set -e

cd /root/camerica/repo/

echo "MOUNTING BOOT PARTITION"
mkdir -p /tmp/bootmnt
mount -t vfat /dev/mmcblk0p1 /tmp/bootmnt

echo "UPDATING KERNEL"
cp camerica_linux/build/zImage /tmp/bootmnt

echo "UPDATING KERNEL MODULES"
tar xzf camerica_linux/build/modules.tar.gz -C /
cp camerica_linux/build/udmabuf.ko ../ko/

echo "UPDATING FPGA CONFIGURATION"
tar xzf camerica_fpga/sd_fat.tar.gz -C /tmp/bootmnt

echo "UNMOUNTING BOOT PARTITION"
sync
umount /tmp/bootmnt
rm -rf /tmp/bootmnt

echo "BUILDING NEON ACCELERATOR"
source ../venv/bin/activate
cd camerica_py/neondraw
python3 neondraw_build.py

echo "COMPONENTS INSTALLED"
echo "Please reboot the system to load the new components."
