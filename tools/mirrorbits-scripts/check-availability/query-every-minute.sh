#!/bin/bash

# Query mirrorbits every minute for a particular file.
# Ask for JSON output.

set -eu

if [ $# -lt 2 ]; then
    echo "Usage: $0 OUTDIR URL1 [URL2...]" >&2
    exit 1
fi

OUTDIR=$1
shift

checkcmds() {
    local cmd
    for cmd in $@; do
        if ! command -v $cmd >/dev/null 2>&1; then
            echo "Please install $cmd. Aborting." >&2
            exit 1
        fi
    done
}

checkcmds jq wget

mkdir -p "$OUTDIR"
cd "$OUTDIR"

get_this() {
    local url=$1
    local fn=$2
    local outdir=
    local data=

    outdir=$(basename $url)

    data=$(wget --header Accept:application/json -q -O- $url) || :
    if [ -z "$data" ]; then
        echo "$outdir/$fn Failed to get file (no data)" >&2
        return
    fi

    data=$(echo "$data" | jq) || :
    if [ -z "$data" ]; then
        echo "$outdir/$fn Failed to parse JSON data" >&2
        return
    fi

    mkdir -p "$outdir"
    echo "$data" > "$outdir/$fn".json
}

# Loop and request files every minute
while true; do
    sleep 1
    if [ $(date -u +%S) -ne 0 ]; then
	continue
    fi
    now=$(date -u +%Y%m%dT%H%M)
    for url in $@; do
        get_this $url $now
    done
    echo -n .
done
