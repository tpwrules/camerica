#!/bin/bash

cd /root/camerica

# shutdown as much as possible
repo/camerica_linux/sysdown > /dev/null 2>&1

# install fuse driver
insmod ko/fuse.ko > /dev/null 2>&1

set -e

# now do udmabuf driver with 32 max-frame-sized buffers
# plus 1 to hold the list of buffers
insmod ko/udmabuf.ko udmabuf0=657408 udmabuf1=657408 udmabuf2=657408 udmabuf3=657408 udmabuf4=657408 udmabuf5=657408 udmabuf6=657408 udmabuf7=657408 udmabuf8=657408 udmabuf9=657408 udmabuf10=657408 udmabuf11=657408 udmabuf12=657408 udmabuf13=657408 udmabuf14=657408 udmabuf15=657408 udmabuf16=657408 udmabuf17=657408 udmabuf18=657408 udmabuf19=657408 udmabuf20=657408 udmabuf21=657408 udmabuf22=657408 udmabuf23=657408 udmabuf24=657408 udmabuf25=657408 udmabuf26=657408 udmabuf27=657408 udmabuf28=657408 udmabuf29=657408 udmabuf30=657408 udmabuf31=657408 

# get python environment set up
source venv/bin/activate

# cd to python work directory
cd repo/camerica_py

set +e
