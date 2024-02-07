#!/usr/bin/python3

import argparse
import json
import logging
import os
import sys

parser = argparse.ArgumentParser(
    description="Analyze mirrorbits JSON replies")
parser.add_argument("-d", "--debug", action="store_true",
    help="print debug messages")
parser.add_argument("DATADIR")
args = parser.parse_args()

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG if args.debug else logging.INFO)

DATADIR = args.DATADIR
if not os.path.isdir(DATADIR):
    log.error("%s: Not a directory", DATADIR)
    sys.exit(1)

DATAFILES = sorted(os.listdir(DATADIR))

for fn in DATAFILES:
    if fn.endswith(".swp"):
        continue

    if not fn.endswith(".json"):
        log.info("Skipping %s (not a .json)", fn)
        continue

    date = os.path.splitext(fn)[0]

    fn = os.path.join(DATADIR, fn)

    if os.stat(fn).st_size == 0:
        log.info("Skipping %s (empty)", fn)
        continue

    log.debug("Doing %s", fn)

    with open(fn) as f:
        data = json.load(f)

    mirrorlist = data['MirrorList']
    excludedlist = data.get('ExcludedList', [])

    n_included = len(mirrorlist)
    n_excluded = len(excludedlist)
    n_total = n_included + n_excluded

    # reasons why the mirror was excluded
    country_only = 0
    file_not_found = 0
    file_size_mismatch = 0
    mod_time_mismatch = 0
    other_reason = 0
    status_code = 0
    unreachable = 0

    for m in excludedlist:
        reason = m['ExcludeReason']
        if "Country only" in reason:
            country_only += 1
        elif "File not found" in reason:
            file_not_found += 1
        elif "File size mismatch" in reason:
            file_size_mismatch += 1
        elif "Mod time mismatch" in reason:
            mod_time_mismatch += 1
        elif "Got status code" in reason:
            status_code += 1
        elif "Unreachable" in reason:
            unreachable += 1
        else:
            other_reason += 1

    fallback = data.get('Fallback', False)
    fallback = 1 if fallback else 0

    print(f"{date} {n_total} {n_included} {n_excluded} {country_only} {file_not_found} {file_size_mismatch} {mod_time_mismatch} {status_code} {unreachable} {other_reason} {fallback}")
