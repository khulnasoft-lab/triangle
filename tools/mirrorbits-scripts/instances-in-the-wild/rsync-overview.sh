#!/bin/bash

set -eu

if [ $# -ne 1 ]; then
    echo "Usage: $(basename $0) DATA_DIR" >&2
    exit 1
fi

cd $1

printf "%14s %8s   %8s %5s   %8s %5s   %8s %5s\n" ID FILES .DEB META .RPM META .TAR.ZST META
for f in *.rsync; do
    n=$(grep '^-' $f | wc -l) # n files

    deb=$(grep '\.deb$' $f | wc -l)              # debian packages
    rpm=$(grep '\.rpm$' $f | wc -l)              # rpm packages
    tar=$(grep '\.pkg\.tar\.zst$' $f | wc -l)    # arch packages

    release=$(grep -E '/(In)?Release$' $f | wc -l) # debian release files
    repomd=$(grep -E '/repomd\.xml$' $f | wc -l)   # rpm repo index
    db=$(grep '\.db\.sig$' $f | wc -l)             # arch db signatures

    installers=$(grep -iE '\.(exe|iso)$' $f | wc -l)

    printf "%14s %'8d | %'8d %'5d | %'8d %'5d | %'8d %'5d" \
        ${f%.*} $n $deb $release $rpm $repomd $tar $db
    #printf " | %'4d" $installers
    echo
done
