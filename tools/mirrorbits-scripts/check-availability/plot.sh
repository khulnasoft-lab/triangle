#!/bin/bash

set -eu

if ! command -v gnuplot >/dev/null 2>&1; then
    echo "Please install gnuplot. Aborting." >&2
    exit 1
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 [analyze-json.dat]" >&2
    exit 1
fi

if [ ! -e "$1" ]; then
    echo "ERROR: Can't find $1" >&2
    exit 1
fi

args=
filename=$(basename ${1%.dat})

if [ "${GITLAB_CI:-}" ]; then
    args="-e png=1"
fi

gnuplot $args -c plot-total.plg $1 $filename
gnuplot $args -c plot-selected-excluded.plg $1 $filename
