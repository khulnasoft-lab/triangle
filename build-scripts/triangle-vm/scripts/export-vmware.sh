#!/bin/sh

set -eu

SCRIPTSDIR=$RECIPEDIR/scripts
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

info "Generate $image.vmdk"
rm -fr $image.vmwarevm && mkdir $image.vmwarevm
qemu-img convert -O vmdk -o subformat=twoGbMaxExtentSparse \
    $image.raw $image.vmwarevm/$image.vmdk

[ $keep -eq 1 ] || rm -f $image.raw

info "Generate $image.vmx"
$SCRIPTSDIR/generate-vmx.sh $image.vmwarevm/$image.vmdk

if [ $zip -eq 1 ]; then
    info "Compress to $image.7z"
    7zr a -sdel -mx=9 $image.7z $image.vmwarevm
fi

for fn in $image.*; do
    [ $(stat -c %Y $fn) -ge $START_TIME ] && echo $fn || :
done > .artifacts
