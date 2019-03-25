#!/bin/bash

cd /root/camerica

# attempt to mount the recordings directory
mkdir -p /root/recordings

mount | grep 'on /root/recordings' > /dev/null
if [ $? -ne 0 ]; then
    # could not find it, so it must not be mounted
    # try to mount /dev/sda1 as a FAT device to it
    echo "MOUNTING RECORDINGS DIRECTORY"
    mount -t vfat /dev/sda1 /root/recordings
    if [ $? -ne 0 ]; then
        echo "COULD NOT MOUNT USB DEVICE. MOUNTING RAM INSTEAD..."
        mount -t tmpfs -o size=128M tmpfs /root/recordings
    fi
else
    echo "RECORDINGS DIRECTORY ALREADY MOUNTED"
fi

# now do udmabuf driver with 32 max-frame-sized buffers
# but only if not already initialized
# if it wasn't initialized correctly, Studio will complain and the user
# can reboot
echo "INITIALIZING DMA BUFFERS"
lsmod | grep udmabuf > /dev/null
if [ $? -ne 0 ]; then
    set -e
    insmod ko/udmabuf.ko udmabuf0=657408 udmabuf1=657408 udmabuf2=657408 udmabuf3=657408 udmabuf4=657408 udmabuf5=657408 udmabuf6=657408 udmabuf7=657408 udmabuf8=657408 udmabuf9=657408 udmabuf10=657408 udmabuf11=657408 udmabuf12=657408 udmabuf13=657408 udmabuf14=657408 udmabuf15=657408 udmabuf16=657408 udmabuf17=657408 udmabuf18=657408 udmabuf19=657408 udmabuf20=657408 udmabuf21=657408 udmabuf22=657408 udmabuf23=657408 udmabuf24=657408 udmabuf25=657408 udmabuf26=657408 udmabuf27=657408 udmabuf28=657408 udmabuf29=657408 udmabuf30=657408 udmabuf31=657408 
fi

echo "LOADING PYTHON"
# get python environment set up
source venv/bin/activate

# cd to python work directory
cd repo/camerica_py

echo "SYSTEM INITIALIZATION COMPLETE"

set +e
