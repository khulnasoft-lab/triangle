#!/bin/sh

set -eu

START_TIME=$(date +%s)

info() { echo "INFO:" "$@"; }

image=
zip=0

while [ $# -gt 0 ]; do
    case $1 in
        -z) zip=1 ;;
        *) image=$1 ;;
    esac
    shift
done

cd $ARTIFACTDIR

info "Rename to $image.img"
mv -v $image.raw $image.img
touch $image.img

if [ $zip -eq 1 ]; then
    info "Dig holes in the sparse file"
    fallocate -v --dig-holes $image.img

    info "Create bmap file $image.img.bmap"
    bmaptool create $image.img > $image.img.bmap

    info "Compress to $image.img.xz"
    xz -f $image.img
fi

for fn in $image.*; do
    [ $(stat -c %Y $fn) -ge $START_TIME ] && echo $fn || :
done > .artifacts
