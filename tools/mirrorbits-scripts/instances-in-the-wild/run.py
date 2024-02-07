#!/usr/bin/python3

import argparse
import logging
import os
import random
import re
import subprocess
import sys
import urllib.request
import yaml

from dataclasses import dataclass
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup


OUTDIR = ""


def parse_last_updated(text):
    # Return how many days the mirror is outdated
    m = re.match(r"(\d+) years? ago", text)
    if m:
        return int(m.group(1)) * 365
    m = re.match(r"(\d+) days? ago", text)
    if m:
        return int(m.group(1))
    return 0


def parse_footer(text):
    # Return mirrorbits version
    m = re.match(r"Mirrorbits (\S+) running on ", text)
    if m:
        return m.group(1)
    return None


def do_mirrorstats(instance, url):
    mirrors = []
    version = None

    # Get the page
    try:
        with urllib.request.urlopen(url) as f:
            html = f.read()
    except urllib.error.URLError as e:
        log.error("URLError: %s", e)
        return mirrors, version

    # Parse the page
    html = BeautifulSoup(html, features="lxml")

    # Get mirrorbits version
    div = html.body.find("div", attrs={"id": "footer"})
    if not div:
        log.error('Couldn\'t find <div id="footer"> in HTML')
    else:
        footer = div.text.strip()
        version = parse_footer(footer)
        log.debug(footer)

    # Get the list of mirrors
    div = html.body.find("div", attrs={"id": "chart"})
    if not div:
        log.error('Couldn\'t find <div id="chart"> in HTML')
    else:
        rows = div.find_all("tr")
        rows = rows[1:]  # remove table header
        for idx, row in enumerate(rows):
            # each mirror takes two rows
            if idx % 2 != 0:
                continue
            cells = row.find_all("td")
            mirror = cells[0].text
            last_updated = cells[2].text
            outdated = parse_last_updated(last_updated)
            item = {
                "name": mirror,
                "outdated": outdated,
            }
            mirrors.append(item)
            log.debug("%s", item)

    # Sort mirrors per name
    mirrors = sorted(mirrors, key=lambda d: d["name"])

    # Save output
    if OUTDIR:
        if not os.path.isdir(OUTDIR):
            os.mkdir(OUTDIR)

        with open(f"{OUTDIR}/{instance}.version", "w") as f:
            f.write(version or "unknown")
            f.write("\n")

        with open(f"{OUTDIR}/{instance}.mirrors", "w") as f:
            f.write("# mirror days-outdated\n")
            for item in mirrors:
                f.write(f"{item['name']} {item['outdated']}\n")

    return mirrors, version


@dataclass
class FileMatch:
    name: str
    endings: List[str]
    count: int = 0


def do_rsync(instance, url):
    n_files = 0
    file_types = {}

    # Run the rsync command
    cmd = [
        "rsync",
        "-r",
        "--no-motd",
        "--timeout=30",
        "--contimeout=30",
        "--exclude=.~tmp~/",
        url,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        log.error("Command failed: %s", " ".join(cmd))
        if p.stderr:
            log.error("%s", p.stderr)
        return n_files, file_types

    # Analyze output
    matchers = [
        FileMatch("arch-pkg", [".pkg.tar.zst"]),
        FileMatch("deb-pkg", [".deb"]),
        FileMatch("rpm-pkg", [".rpm"]),
        FileMatch("arch-meta", [".db.tar.zst"]),
        FileMatch("deb-meta", ["/InRelease", "/Release"]),
        FileMatch("rpm-meta", ["/repomd.xml"]),
    ]

    for line in p.stdout.splitlines():
        # skip directories
        if line.startswith("d"):
            continue
        n_files += 1
        path = line.split(maxsplit=5)[4]
        for m in matchers:
            match = False
            for e in m.endings:
                if path.endswith(e):
                    match = True
                    m.count += 1
                    break
            if match:
                break

    for m in matchers:
        file_types[m.name] = m.count

    # Save output
    if OUTDIR:
        if not os.path.isdir(OUTDIR):
            os.mkdir(OUTDIR)

        with open(f"{OUTDIR}/{instance}.rsync", "w") as f:
            f.write(p.stdout)

    return n_files, file_types


def process_instance(instance, data, rsync=False):
    # Get and process mirrorstats
    mirrors = []
    version = None
    if True:
        url = data["mirrorstats"]
        log.info("Fetching page: %s ...", url)
        mirrors, version = do_mirrorstats(instance, url)
        log.info(f"Mirrorbits version: {version or 'unknown'}")
        log.info(f"Number of mirrors : {len(mirrors)}")

    # Get and process mirrorlist - NOT IMPLEMENTED!
    if False:
        url = data["mirrorlist"]
        mirrors, version = do_mirrorlist(instance, url)
        # todo: https/http variant

    # List files on the mirror via rsync
    n_files = 0
    file_types = {}
    if rsync is True:
        urls = data["rsync"]
        random.shuffle(urls)
        for url in urls:
            log.info("Listing files: %s ...", url)
            n_files, file_types = do_rsync(instance, url)
            if n_files != 0:
                break
        log.info(f"Number of files: {n_files:,}")

    return {
        "version": version,
        "mirrors": mirrors,
        "n_files": n_files,
        "file_types": file_types,
    }


# printing --------------------------------------------------------------------


@dataclass
class Column:
    header: str
    alignment: str
    enabled: bool = False
    width: int = 0


def print_markdown_table(instances_data):
    # How to format the 'since' column
    # TIME_FORMAT = "%B %Y"  # pretty but doesn't sort
    TIME_FORMAT = "%Y-%m"  # not the most pretty, but it sorts

    # Whether we want HTML links in the output
    WITH_LINKS = True

    # Whether to show the "Linux Distros" column
    WITH_DISTRO_INFO = True

    # Whether to show the "Files" column (useful to debug)
    WITH_FILES_INFO = False

    # If a mirror is outdated for longer than that, consider it's not an
    # active mirror.
    MIRROR_ACTIVE_THRESHOLD = 30  # days

    # If a mirror has more packages than that, consider it's a full distro
    # (as opposed to partial repo, which only provides some packages).
    FULL_DISTRO_THRESHOLD = 10000

    items_to_print = []

    #
    # First pass: prepare text to display
    #

    count = 0
    for inst, data in instances_data.items():
        count += 1

        # Instance name
        name = data.get("name", inst.capitalize())
        if WITH_LINKS:
            name = f"[{name}][{count:02}a]"

        # Since when mirrorbits was setup
        since = data.get("since", None)
        if since:
            since = since["date"].strftime(TIME_FORMAT)
            if WITH_LINKS:
                since = f"[{since}][{count:02}b]"
        else:
            since = "unknown"

        # Whether the instance is in prod
        prod = "✓" if data["prod"] else "✗"

        out = data["output"]

        # Mirrorbits version
        version = out["version"] or "unknown"

        # Number of mirrors (total and active)
        mirrors = out["mirrors"]
        mir = len(mirrors)
        act = 0
        for item in mirrors:
            if item["outdated"] < MIRROR_ACTIVE_THRESHOLD:
                act += 1

        # Number of files on the mirror
        files = out["n_files"]
        if files >= 1000:
            files = round(files / 1000)
            files = f"{files}k"
        else:
            files = str(files)

        # File types
        distro_files = {}
        full_distro = []
        partial_repo = []
        file_types = out["file_types"]
        for dist in ["arch", "deb", "rpm"]:
            meta = file_types.get(f"{dist}-meta", 0)
            pkg = file_types.get(f"{dist}-pkg", 0)
            if meta == 0 and pkg == 0:
                continue
            distro_files[dist] = {"pkg": pkg, "meta": meta}
            # must have both packages and metadata to be a distro
            if meta == 0 or pkg == 0:
                continue
            # let's find out if it's a partial repo or a full distro
            distro_type = data.get("distro", None)
            if distro_type is None:
                # crude heuristic
                if pkg >= FULL_DISTRO_THRESHOLD:
                    distro_type = "full"
                else:
                    distro_type = "partial"
            if distro_type == "full":
                full_distro.append(dist)
            elif distro_type == "partial":
                partial_repo.append(dist)
            else:
                log.error("Invalid distro type: %s", distro_type)

        # Make the short comment
        distro_info = ""
        if WITH_DISTRO_INFO:
            elems = []
            if full_distro:
                line = "full distro: " + ", ".join(full_distro)
                elems.append(line)
            if partial_repo:
                line = "partial repo: " + ", ".join(partial_repo)
                elems.append(line)
            distro_info = ", ".join(elems)

        # Make the longer details
        files_info = ""
        if WITH_FILES_INFO:
            elems = []
            for dist, val in distro_files.items():
                line = f"{dist}: pkg={val['pkg']}, meta={val['meta']}"
                elems.append(line)
            files_info = " / ".join(elems)

        # Done
        item = [name, since, prod, mir, act, files, version, distro_info, files_info]
        items_to_print.append(item)

    #
    # Second pass: compute columns width, hide empty columns
    #

    COLUMNS = [
        Column("Instance", "left"),
        Column("Since", "right"),
        Column("Prod", "right"),
        Column("Mir", "right"),
        Column("Act", "right"),
        Column("Files", "right"),
        Column("Version", "left"),
        Column("Linux Distros", "left"),
        Column("Files", "left"),
    ]

    header_item = [c.header for c in COLUMNS]

    def update_width(item):
        for i, v in enumerate(item):
            col = COLUMNS[i]
            l = len(str(v))
            if l > col.width:
                col.width = l

    # Compute the width for each column
    update_width(header_item)
    for item in items_to_print:
        update_width(item)

    # Hide columns if ever they're empty
    for item in items_to_print:
        for i, v in enumerate(item):
            col = COLUMNS[i]
            if col.enabled:
                continue
            if str(v) in ["", "0"]:
                continue
            col.enabled = True

    #
    # Last pass: print
    #

    def print_line(item):
        for i, v in enumerate(item):
            col = COLUMNS[i]
            if not col.enabled:
                continue
            l = col.width
            if col.alignment == "right":
                print(f"| {v:>{l}} ", end="")
            else:
                print(f"| {v:<{l}} ", end="")
        print("|")

    def print_sep():
        for col in COLUMNS:
            if not col.enabled:
                continue
            l = col.width
            v = ":"
            if col.alignment == "right":
                print(f"| {v:->{l}} ", end="")
            else:
                print(f"| {v:-<{l}} ", end="")
        print("|")

    # Print the table
    print()
    print_line(header_item)
    print_sep()
    for item in items_to_print:
        print_line(item)

    # Print the links
    if WITH_LINKS:
        print()
        count = 0
        for inst, data in instances_data.items():
            count += 1
            print(f"[{count:02}a]: {data['homepage']}")
            if "since" in data:
                print(f"[{count:02}b]: {data['since']['url']}")


# main ------------------------------------------------------------------------


parser = argparse.ArgumentParser(
    description="Details on mirrorbits instances in the wild")
parser.add_argument("-d", "--debug", action="store_true",
    help="print debug messages")
parser.add_argument("-i", "--include", action="append",
    help="process only this instance (can be set multiple times)")
parser.add_argument("-o", "--outdir",
    help="dump a lot of data into outdir")
parser.add_argument("-r", "--rsync", action="store_true",
    help="enable rsync listing (takes a while)")
parser.add_argument("-x", "--exclude", action="append",
    help="exclude this instance (can be set multiple times)")
parser.add_argument("YAML_FILE")
args = parser.parse_args()

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG if args.debug else logging.INFO)

OUTDIR = args.outdir

with open(args.YAML_FILE, "r") as f:
    yaml_data = yaml.safe_load(f)

output = {}
for inst, data in yaml_data.items():
    if args.include and inst not in args.include:
        log.debug(">>> Skip %s (not included)", inst)
        continue

    if args.exclude and inst in args.exclude:
        log.debug(">>> Skip %s (excluded)", inst)
        continue

    log.info(">>> Process %s", inst)
    result = process_instance(inst, data, rsync=args.rsync)
    output[inst] = data
    output[inst]["output"] = result

print_markdown_table(output)
