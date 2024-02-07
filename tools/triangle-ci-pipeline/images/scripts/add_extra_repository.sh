#!/bin/bash
# Copyright salsa-ci-team and others
# SPDX-License-Identifier: FSFAP
# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved. This file is offered as-is, without any warranty.

# Add an extra apt repository sources.list if the extra-repository argument is
# set. The extra_repository and extra_repository_key variables are filenames.
# The optional target-etc argument allows setting a different destination path
# to be able to update chroots.
# Passing the update flag will cause the script to call apt-get update at the
# end if the file was added.

SALSA_CI_EXTRA_REPOSITORY=""
SALSA_CI_EXTRA_REPOSITORY_KEY=""
TARGET_ETC="/etc"
VERBOSE=0

while [[ "$#" -ge 1 ]]; do
    case "$1" in
        --extra-repository|-e)
            shift
            SALSA_CI_EXTRA_REPOSITORY="$1"
            shift
            ;;
        --extra-repository-key|-k)
            shift
            SALSA_CI_EXTRA_REPOSITORY_KEY="$1"
            shift
            ;;
        --target-etc|-t)
            shift
            TARGET_ETC="$1"
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
    esac
done

if [[ "$VERBOSE" -ne 0 ]]; then
    set -x
fi

if [[ -n "${SALSA_CI_EXTRA_REPOSITORY}" ]]; then
    mkdir -p "${TARGET_ETC}"/apt/sources.list.d/
    cp "${SALSA_CI_EXTRA_REPOSITORY}" \
        "${TARGET_ETC}"/apt/sources.list.d/extra_repository.list
    if [[ -n "${SALSA_CI_EXTRA_REPOSITORY_KEY}" ]]; then
        mkdir -p "${TARGET_ETC}"/apt/trusted.gpg.d/
        cp "${SALSA_CI_EXTRA_REPOSITORY_KEY}" \
            "${TARGET_ETC}"/apt/trusted.gpg.d/extra_repository.asc
    fi
    apt-get update
    apt-get upgrade --assume-yes
    apt-get --assume-yes install ca-certificates
fi

