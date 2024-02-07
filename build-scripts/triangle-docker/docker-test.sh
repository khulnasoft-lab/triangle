#!/bin/bash

set -e
set -u

IMAGE=$1
ARCHITECTURE=$2

# Retrieve variables from former docker-build.sh
. ./"$IMAGE-$ARCHITECTURE".conf

# Get corresponding machine hardware name
case "$ARCHITECTURE" in
    amd64) MACHINE="x86_64" ;;
    armel) MACHINE="armv7l" ;;
    arm64) MACHINE="aarch64";;
    armhf) MACHINE="armv7l" ;;
    i386)  MACHINE="x86_64" ;;
esac

if [ "$REGISTRY" != localhost ]; then
    podman pull "$REGISTRY_IMAGE/$IMAGE:$TAG"
fi

MACH=$(podman run --rm "$REGISTRY_IMAGE/$IMAGE:$TAG" uname -m)
if [ "$MACH" = "$MACHINE" ]; then
    echo "OK: Got expected machine hardware name '$MACH'"
else
    echo "ERROR: Incorrect machine hardware name '$MACH' (expected '$MACHINE')" >&2
    exit 1
fi

DPKG_ARCH=$(podman run --rm "$REGISTRY_IMAGE/$IMAGE:$TAG" dpkg --print-architecture)
if [ "$DPKG_ARCH" = "$ARCHITECTURE" ]; then
    echo "OK: Got expected dpkg architecture '$DPKG_ARCH'"
else
    echo "ERROR: Incorrect dpkg architecture '$DPKG_ARCH' (expected '$ARCHITECTURE')" >&2
    exit 1
fi
