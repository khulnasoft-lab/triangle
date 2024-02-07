#!/usr/bin/env bash
#
# ./$0
# http_proxy= ./$0
#
# REF:
# - https://gitlab.com/kalilinux/build-scripts/kali-docker/-/blob/master/build-rootfs.sh
# - https://gitlab.com/kalilinux/nethunter/build-scripts/kali-nethunter-project/-/blob/master/nethunter-fs/stages/stage1
#

set -eu

KNOWN_CACHING_PROXIES="\
3142 apt-cacher-ng
8000 squid-deb-proxy"
DETECTED_CACHING_PROXY=

SUPPORTED_ARCHITECTURES="amd64 arm64"
SUPPORTED_BRANCHES="kali-rolling kali-dev kali-last-snapshot"
SUPPORTED_DESKTOPS="e17 gnome i3 kde lxde mate xfce none"
SUPPORTED_TOOLSETS="default everything headless large none"

DEFAULT_ARCH=amd64
DEFAULT_BRANCH=kali-rolling
DEFAULT_DESKTOP=none
DEFAULT_MIRROR=http://http.kali.org/kali
DEFAULT_TOOLSET=none

ARCH=
BRANCH=
DESKTOP=
KEEP=false
MIRROR=
PACKAGES=
TOOLSET=
VERSION=
VARIANT=WSL
OUTDIR="$( pwd )/output"
PROMPT=#

default_toolset() { [ ${DESKTOP:-$DEFAULT_DESKTOP} = none ] && echo none || echo ${DEFAULT_TOOLSET}; }
default_version() { echo ${BRANCH:-$DEFAULT_BRANCH} | sed "s/^kali-//"; }

## Output bold only if both stdout/stderr are opened on a terminal
if [ -t 1 ] && [ -t 2 ]; then
  b() { tput bold; echo -n "$@"; tput sgr0; }
else
  b() { echo -n "$@"; }
fi
vrun() { echo -n "[$( date -u +'%H:%M:%S' )] ${VARIANT}:~${PROMPT} "; b "$@"; echo; $@; }
warn() { echo "WARNING: " "$@" 1>&2; }
fail() { echo "ERROR: "   "$@" 1>&2; exit 1; }

kali_message() {
  local line=
  echo   "┏━━($( b $@ ))"
  while IFS= read -r line; do
    echo "┃ ${line}";
  done
  echo   "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

ask_confirmation() {
  local question=${1:-"Do you want to continue?"}
  local default=yes
  local default_verbing=
  local choices=
  local grand_timeout=60
  local timeout=20
  local time_left=
  local answer=
  local ret=

  ## If stdin is closed, no need to ask, assume yes
  [ -t 0 ] || return 0

  ## Set variables that depend on default
  if [ ${default} = yes ]; then
    default_verbing=proceeding
    choices="[Y/n]"
  else
    default_verbing=aborting
    choices="[y/N]"
  fi

  ## Discard chars pending on stdin
  while read -r -t 0; do read -r; done

  ## Ask the question, allow for X timeouts before proceeding anyway
  grand_timeout=$(( grand_timeout - timeout ))
  for time_left in $( seq ${grand_timeout} -${timeout} 0 ); do
    ret=0
    read -r -t ${timeout} -p "${question} ${choices} " answer \
      || ret=$?
    if [ ${ret} -gt 128 ]; then
      if [ ${time_left} -gt 0 ]; then
        echo "...${time_left} seconds left before ${default_verbing}"
      else
        echo "...No answer, assuming ${default}, ${default_verbing}"
      fi
      continue
    elif [ ${ret} -gt 0 ]; then
      exit ${ret}
    else
      break
    fi
  done

  ## Process the answer
  [ "${answer}" ] && answer=${answer} || answer=${default}
  case "${answer}" in
    y|yes) return 0;;
    *)     return 1;;
  esac
  echo ""
}

## check_os
check_os() {
  [ -e "/usr/share/debootstrap/scripts/${BRANCH}" ] \
    || fail "debootstrap has no script for: ${BRANCH}. Need to use a newer debootstrap"

  [ -e "/usr/share/keyrings/kali-archive-keyring.gpg" ] \
    || fail "Missing /usr/share/keyrings/kali-archive-keyring.gpg (See README.md -> Non-Kali Debian-Based Environment)"
}

## rootfs_chroot <cmd>
rootfs_chroot() {
  echo "[$( date -u +'%H:%M:%S' )] (chroot) ${VARIANT}:~${PROMPT} $( b "$@" )"
  PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    chroot "${rootfsDir}" "$@"
}

## debootstrap_log <ret>
debootstrap_log() {
  if [ "${1}" != 0 ]; then
    warn "debootstrap: exit $1"
    [ -e "${rootfsDir}"/debootstrap/debootstrap.log ] && \
      tail -v "${rootfsDir}"/debootstrap/debootstrap.log
    exit "${1}"
  fi
}

## create_rootfs
create_rootfs() {
  export LC_ALL=C
  ## Workaround for https://bugs.launchpad.net/ubuntu/+bug/520465
  export MALLOC_CHECK_=0

  vrun mkdir -pv "${OUTDIR}/"
  rootfsDir="$( mktemp -d )"

  cmd_args=""
  ## If we are using a foreign architecture (e.g. arm64 on amd64) we are opt'ing to do debootstrap in 2 stages
  ## Newer versions of debootstrap may be auto handle this in the future
  if (
       ([ "$( uname -m )" != "aarch64" ] && [ "${ARCH}" == "arm64" ]) ||
       ([ "$( uname -m )" != "x86_64"  ] && [ "${ARCH}" == "amd64" ])
     ); then
    echo "[i] Foreign architecture: $( uname -m ) machine for ${ARCH} rootfs"
    cmd_args="--foreign"
  fi
  ret=0
  ## Install all packages of priority required and important, including apt. Skipping: --variant=minbase
  vrun /usr/sbin/debootstrap \
      ${cmd_args} \
      --arch "${ARCH}" \
      --components=main,contrib,non-free,non-free-firmware \
      --include=kali-archive-keyring \
      "${BRANCH}" \
      "${rootfsDir}"/ \
      "${MIRROR}" \
    || debootstrap_log "$?"

  if (
       ([ "$( uname -m )" != "aarch64" ] && [ "${ARCH}" == "arm64" ]) ||
       ([ "$( uname -m )" != "x86_64"  ] && [ "${ARCH}" == "amd64" ])
     ); then
    if [ "$( uname -m )" != "aarch64" ] && [ "${ARCH}" == "arm64" ]; then
      vrun cp -v /usr/bin/qemu-aarch64-static "${rootfsDir}"/usr/bin
    elif [ "$( uname -m )" != "x86_64" ] && [ "${ARCH}" == "amd64" ]; then
      vrun cp -v /usr/bin/qemu-x86_64-static "${rootfsDir}"/usr/bin
    else
      fail "Unsure of cross-build architecture: $( uname -m ) / ${ARCH}"
    fi
    ret=0
    rootfs_chroot /debootstrap/debootstrap \
        --second-stage \
      || debootstrap_log "$?"
  fi

  echo "[i] Setting shell profile"
  cat << EOF > "${rootfsDir}"/etc/profile
# /etc/profile: system-wide .profile file for the Bourne shell (sh(1))
# and Bourne compatible shells (bash(1), ksh(1), ash(1), ...).

# WSL already sets PATH, shouldn't be overridden
IS_WSL=\$( grep -i microsoft /proc/version )
if test "\${IS_WSL}" = ""; then
  if [ "\$( id -u )" -eq 0 ]; then
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  else
    PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"
  fi
fi
export PATH

if [ "$\{PS1-}" ]; then
  if [ "\${BASH-}" ] && [ "\${BASH}" != "/bin/sh" ]; then
    # The file bash.bashrc already sets the default PS1.
    # PS1='\h:\w$ '
    if [ -f /etc/bash.bashrc ]; then
      . /etc/bash.bashrc
    fi
  else
    if [ "\$( id -u )" -eq 0 ]; then
      PS1='# '
    else
      PS1='$ '
    fi
  fi
fi

if [ -d /etc/profile.d ]; then
  for i in /etc/profile.d/*.sh; do
    if [ -r \$i ]; then
      . \$i
    fi
  done
  unset i
fi
EOF

 #rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install kali-defaults # Skipping: --no-install-recommends
  rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install kali-linux-wsl

  [ "${TOOLSET}" != "none" ] && \
    rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install kali-linux-${TOOLSET}
  [ "${DESKTOP}" != "none" ] && \
    rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install kali-desktop-${DESKTOP} xorg xrdp
  [ "${PACKAGES}" ] && \
    rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install ${PACKAGES}

  if [ "${DESKTOP}" != "none" ]; then
    echo "[i] Switching xrdp to use 3390/TCP"
    vrun sed -i 's/port=3389/port=3390/g' "${rootfsDir}"/etc/xrdp/xrdp.ini
  fi

  ## Using pipes with vrun doesn't work too well
  #echo "deb ${DEFAULT_MIRROR} ${BRANCH} main contrib non-free non-free-firmware" > "${rootfsDir}"/etc/apt/sources.list
  cat << EOF > "${rootfsDir}"/etc/apt/sources.list
# See: https://www.kali.org/docs/general-use/kali-linux-sources-list-repositories/
deb ${DEFAULT_MIRROR} ${BRANCH} main contrib non-free non-free-firmware

# Additional line for source packages
#deb-src ${DEFAULT_MIRROR} ${BRANCH} main contrib non-free non-free-firmware
EOF
  echo "kali" > "${rootfsDir}"/etc/hostname
  #echo "127.0.0.1 localhost" > "${rootfsDir}"/etc/hosts
  cat << EOF > "${rootfsDir}"/etc/hosts
127.0.0.1 localhost
::1   localhost ip6-localhost ip6-loopback
ff02::1   ip6-allnodes
ff02::2   ip6-allrouters
EOF
  vrun truncate -s 0 "${rootfsDir}"/etc/resolv.conf

  ## Clean - APT packages
  rootfs_chroot env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes clean
  vrun rm -vrf "${rootfsDir}"/var/lib/apt/lists/*
  vrun mkdir -vp "${rootfsDir}"/var/lib/apt/lists/partial
  ## Clean - Logs
  ! "${KEEP}" && \
    vrun find "${rootfsDir}"/var/log -depth -type f -exec truncate -s 0 {} +
  ## Clean - qemu
  (
    ([ "$( uname -m )" != "aarch64" ] && [ "${ARCH}" == "arm64" ]) ||
    ([ "$( uname -m )" != "x86_64"  ] && [ "${ARCH}" == "amd64" ])
  ) && \
     vrun rm -vf "${rootfsDir}"/usr/bin/qemu*
  ## Clean - Misc
  vrun rm -vf "${rootfsDir}"/var/cache/ldconfig/aux-cache

  vrun pushd "${rootfsDir}/"
  ## Skipping tar -v: too noisy
  ## Skipping tar -C "${rootfsDir}"/ / --exclude=./: Due './' being added (tar -tvfj output/*tar.gz | sort -k 9 | head)
  vrun tar --ignore-failed-read --xattrs -czf "${OUTDIR}/${OUTPUT}.tar.gz" ./"*"
  vrun popd

  if ! "${KEEP}"; then
    ## Skipping rm -v - too noisy
    vrun rm -rf "${rootfsDir}"/
  fi
}

USAGE="Usage: $( basename $0 ) <options>

Build a Kali Linux ${VARIANT} rootfs

Build options:
  -a ARCH     Build an rootfs for this architecture, default: $( b ${DEFAULT_ARCH} )
              Supported values: ${SUPPORTED_ARCHITECTURES}
  -b BRANCH   Kali branch used to build the rootfs, default: $( b ${DEFAULT_BRANCH} )
              Supported values: ${SUPPORTED_BRANCHES}
  -k          Keep intermediary build artifacts
  -m MIRROR   Mirror used to build the rootfs, default: $( b ${DEFAULT_MIRROR} )
  -x VERSION  What to name the rootfs release as, default: $( b $( default_version ) )

Customization options:
  -D DESKTOP  Desktop environment installed in the rootfs, default: $( b ${DEFAULT_DESKTOP} )
              Supported values: ${SUPPORTED_DESKTOPS}
  -P PACKAGES Install extra packages (comma/space separated list)
  -T TOOLSET  The selection of tools to include in the rootfs, default: $( b $( default_toolset ) )
              Supported values: ${SUPPORTED_TOOLSETS}

Supported environment variables:
  http_proxy  HTTP proxy URL, refer to the README.md for more details

Refer to the README.md for examples"

while getopts ":a:b:D:f:hkL:m:P:r:s:T:U:v:x:zZ:" opt; do
  case ${opt} in
    (a) ARCH=${OPTARG};;
    (b) BRANCH=${OPTARG};;
    (D) DESKTOP=${OPTARG};;
    (h) echo "${USAGE}"; exit 0;;
    (k) KEEP=true;;
    (m) MIRROR=${OPTARG};;
    (P) PACKAGES="${PACKAGES} ${OPTARG}";;
    (T) TOOLSET=${OPTARG};;
    (x) VERSION=${OPTARG};;
    (*) echo "${USAGE}" 1>&2; exit 1;;
  esac
done
shift $((OPTIND - 1))

## If there isn't any variables setup, use default
[ "${ARCH}"    ] || ARCH=${DEFAULT_ARCH}
[ "${BRANCH}"  ] || BRANCH=${DEFAULT_BRANCH}
[ "${DESKTOP}" ] || DESKTOP=${DEFAULT_DESKTOP}
[ "${MIRROR}"  ] || MIRROR=${DEFAULT_MIRROR}
[ "${TOOLSET}" ] || TOOLSET=$( default_toolset )
[ "${VERSION}" ] || VERSION=$( default_version )

TOOLSET="$( echo ${TOOLSET} | sed 's/kali-linux-//' )"

case $( echo ${ARCH}| tr '[:upper:]' '[:lower:]' ) in
  x64|x86_64|x86-64|amd64)
    ARCH=amd64
    ;;
  arm64|aarch64)
    ARCH=arm64
    ;;
esac

case ${BRANCH} in
  kali-last-release|kali-last-snapshot)
    BRANCH=kali-last-snapshot
    ;;
esac

## Order packages alphabetically, separate each package with ", "
PACKAGES=$( echo ${PACKAGES} | sed "s/[, ]\+/\n/g" | LC_ALL=C sort -u \
  | awk 'ORS=", "' | sed "s/[, ]*$//" )

## Filename structure for final file
OUTPUT=$( echo "kali-linux-${VERSION}-${VARIANT}-rootfs-${ARCH}" | tr '[:upper:]' '[:lower:]' )

## Validate some options
echo "${SUPPORTED_BRANCHES}" | grep -qw "${BRANCH}" \
  || fail "Unsupported branch: ${BRANCH}"
echo "${SUPPORTED_DESKTOPS}" | grep -qw "${DESKTOP}" \
  || fail "Unsupported desktop: ${DESKTOP}"
echo "${SUPPORTED_TOOLSETS}" | grep -qw "${TOOLSET}" \
  || fail "Unsupported toolset: ${TOOLSET}"
echo "${SUPPORTED_ARCHITECTURES}" | grep -qw "${ARCH}" \
  || fail "Unsupported architecture: ${ARCH}"

## Check environment variables for http_proxy
## [ -v ... ] isn't supported on all every bash version
if ! [ $( env | grep http_proxy ) ]; then
  ## Attempt to detect well-known http caching proxies on localhost,
  ## cf. bash(1) section "REDIRECTION". This is not bullet-proof.
  while read port proxy; do
    (</dev/tcp/localhost/${port}) 2>/dev/null || continue
    DETECTED_CACHING_PROXY="${port} ${proxy}"
## Docker: host.docker.internal TODO
    export http_proxy="http://127.0.0.1:${port}"
    break
  done <<< "${KNOWN_CACHING_PROXIES}"
fi

check_os

if [ $( id -u ) -ne 0 ]; then
  PROMPT=$
  warn "This script requires certain privileges"
  warn "Please consider running it using the root user"
  echo ""
fi

## Print a summary
{
echo "# Proxy configuration:"
if [ "${DETECTED_CACHING_PROXY}" ]; then
  read port proxy <<< ${DETECTED_CACHING_PROXY}
  echo " * Detected caching proxy $( b ${proxy} ) on port $( b ${port} )"
elif [ "${http_proxy:-}" ]; then
  echo " * Using proxy via environment variable: $( b http_proxy=${http_proxy} )"
else
  echo " * $( b No HTTP proxy ) configured, all packages will be downloaded from the Internet"
fi

echo "# ${VARIANT} rootfs output:"
echo " * Build a Kali Linux ${VARIANT} rootfs for $( b ${ARCH} ) architecture"
echo "# Build options:"
[ "${MIRROR}"   ] && echo " * Build mirror: $( b ${MIRROR} )"
[ "${BRANCH}"   ] && echo " * Branch: $( b ${BRANCH} )"
[ "${VERSION}"  ] && echo " * Version: $( b ${VERSION} )"
[ "${DESKTOP}"  ] && echo " * Desktop environment: $( b ${DESKTOP} )"
[ "${TOOLSET}"  ] && echo " * Tool selection: $( b ${TOOLSET} )"
[ "${PACKAGES}" ] && echo " * Additional packages: $( b ${PACKAGES} )"
  "${KEEP}"       && echo " * Keep temporary files: $( b ${KEEP} )"
} | kali_message "Kali Linux ${VARIANT} rootfs"

## Ask for confirmation before starting the build
ask_confirmation || { echo "Abort"; exit 1; }

## Build
create_rootfs

## Finish
cat << EOF
..............
            ..,;:ccc,.
          ......''';lxO.
.....''''..........,:ld;
           .';;;:::;,,.x,
      ..'''.            0Xxoc:,.  ...
  ....                ,ONkc;,;cokOdc',.
 .                   OMo           ':$( b dd )o.
                    dMc               :OO;
                    0M.                 .:o.
                    ;Wd
                     ;XO,
                       ,d0Odlc;,..
                           ..',;:cdOOd::,.
                                    .:d;.':;.
                                       'd,  .'
                                         ;l   ..
                                          .o
                                            c
                                            .'
                                             .
Successful build! The following build artifacts were produced:
EOF
## /recipes/ is due to container volume mount
find "${OUTDIR}/" -maxdepth 1 -type f -name "${OUTPUT}*" | sed 's_^/recipes/__;
                                                                s_^_* _'
