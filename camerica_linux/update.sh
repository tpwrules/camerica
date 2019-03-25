#!/bin/bash

cd /root/camerica/repo

echo "UPDATING REPO"
git pull --ff-only | tee /tmp/repo_status

grep 'Already up-to-date.' /tmp/repo_status > /dev/null

if [ $? -eq 0 ]; then
    exit 0
fi

echo "INSTALLING UPDATED COMPONENTS"
bash camerica_linux/install_components.sh
