#!/bin/sh

set -eu

fallocate -v -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
echo "/swapfile none swap defaults 0 0" >> /etc/fstab
