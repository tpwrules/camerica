#!/bin/bash

# we need to mount the boot partition
mkdir /tmp/bootmount
mount -t vfat /dev/mmcblk0p1 /tmp/bootmount

echo "Updating..."
tar xvf $1 -C /tmp/bootmount/
RESULT=$?

sync
umount /tmp/bootmount/
rm -r /tmp/bootmount/

if [ $RESULT -ne 0 ]; then
	echo "Update failed!"
else
	echo "Update successful! Please reboot to load the new configuration."
fi
