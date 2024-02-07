#!/bin/sh

set -eu

# Validate arguments

[ $# -eq 2 ] || usage

disk_path=$1
output=$2

[ ${disk_path##*.} = vhdx ] || fail "Invalid input file '$disk_path'"

description_template=$RECIPEDIR/scripts/templates/vm-description.txt
powershell_template=$RECIPEDIR/scripts/templates/hyperv-powershell.ps1

# Prepare all the values

disk_file=$(basename $disk_path)
name=${disk_file%.*}

arch=${name##*-}
[ "$arch" ] || fail "Failed to get arch from image name '$name'"
version=$(echo $name | sed -E 's/^kali-linux-(.+)-.+-.+$/\1/')
[ "$version" ] || fail "Failed to get version from image name '$name'"

case $arch in
    amd64) platform=x64 ;;
    i386)  platform=x86 ;;
    *)
        fail "Invalid architecture '$arch'"
        ;;
esac

description=$(sed \
    -e "s|%date%|$(date --iso-8601)|g" \
    -e "s|%kbdlayout%|US keyboard layout|g" \
    -e "s|%platform%|$platform|g" \
    -e "s|%version%|$version|g" \
    $description_template)

sed \
    -e "s|%Name%|$name|g" \
    -e "s|%VHDPath%|$disk_path|g" \
    $powershell_template > $output

awk -v r="$description" '{ gsub(/%Description%/,r); print }' $output > $output.1
mv $output.1 $output
