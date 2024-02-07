#!/bin/sh

set -eu

START_TIME=$(date +%s)

info() { echo "INFO:" "$@"; }

image=
keep=0
zip=0

while [ $# -gt 0 ]; do
    case $1 in
        -k) keep=1 ;;
        -z) zip=1 ;;
        *) image=$1 ;;
    esac
    shift
done

cd $ARTIFACTDIR

info "Generate $image.qcow2"
qemu-img convert -O qcow2 $image.raw $image.qcow2

[ $keep -eq 1 ] || rm -f $image.raw

if [ $zip -eq 1 ]; then
    info "Compress to $image.7z"
    7zr a -sdel -mx=9 $image.7z $image.qcow2
fi

for fn in $image.*; do
    [ $(stat -c %Y $fn) -ge $START_TIME ] && echo $fn || :
done > .artifacts
