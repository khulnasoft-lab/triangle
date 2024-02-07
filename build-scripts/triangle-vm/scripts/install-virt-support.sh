#!/bin/sh

set -eu

variant=$1

pkg_installed() {
    dpkg -s "$1" 2>/dev/null | grep -q "ok installed"
}

if pkg_installed kali-desktop-core; then
    hyperv="hyperv-daemons xrdp"
    if pkg_installed pipewire; then
        hyperv="$hyperv pipewire-module-xrdp"
    elif pkg_installed pulseaudio; then
        hyperv="$hyperv pulseaudio-module-xrdp"
    fi
    qemu="qemu-guest-agent spice-vdagent"
    virtualbox="virtualbox-guest-x11"
    vmware="open-vm-tools-desktop"
else
    hyperv="hyperv-daemons"
    qemu="qemu-guest-agent"
    virtualbox="virtualbox-guest-utils"
    vmware="open-vm-tools"
fi

generic=$(echo $hyperv $qemu $virtualbox $vmware \
    | sed "s/ \+/\n/g" | LC_ALL=C sort -u \
    | awk 'ORS=" "' | sed "s/ *$//")

case $variant in
    hyperv)     pkgs=$hyperv ;;
    qemu)       pkgs=$qemu ;;
    virtualbox) pkgs=$virtualbox ;;
    vmware)     pkgs=$vmware ;;
    generic)    pkgs=$generic ;;
    *)
        echo "ERROR: invalid variant '$variant'"
        exit 1
        ;;
esac

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y $pkgs
apt-get clean
