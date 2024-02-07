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
qemu-img convert -O vmdk -o subformat=streamOptimized $image.raw $image.vmdk

[ $keep -eq 1 ] || rm -f $image.raw

info "Generate $image.ovf"
$SCRIPTSDIR/generate-ovf.sh $image.vmdk

info "Generate $image.mf"
$SCRIPTSDIR/generate-mf.sh $image.ovf $image.vmdk

# An OVA is simply a tar archive. The .ovf must come first,
# then the .mf comes either second or last. For details,
# refer to the OVF spec: https://www.dmtf.org/dsp/DSP0243.
info "Generate $image.ova"
tar -cvf $image.ova $image.ovf $image.vmdk $image.mf

[ $keep -eq 1 ] || rm -f $image.ovf $image.vmdk $image.mf

# Since the disk is already compressed (streamOptimized means
# deflate compression with zlib),  there's nothing to gain by
# compressing the .ova again. So we ignore the '-z' option.
if [ $zip -eq 1 ]; then
    info "Disk already compressed, ignoring -z option"
fi

for fn in $image.*; do
    [ $(stat -c %Y $fn) -ge $START_TIME ] && echo $fn || :
done > .artifacts
