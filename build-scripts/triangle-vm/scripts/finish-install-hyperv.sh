#!/bin/sh

set -e

pkg_installed() {
    dpkg -s "$1" 2>/dev/null | grep -q "ok installed"
}

# Bail out if xrdp is not installed
if ! pkg_installed xrdp; then
    exit 0
fi

# Enable the xrdp services
cd /etc/systemd/system/multi-user.target.wants
ln -s /lib/systemd/system/xrdp.service
ln -s /lib/systemd/system/xrdp-sesman.service

# Configure xrdp
# XXX Do it with kali-tweaks when it supports non-interactive mode
/usr/lib/kali_tweaks/helpers/hyperv-enhanced-mode enable
