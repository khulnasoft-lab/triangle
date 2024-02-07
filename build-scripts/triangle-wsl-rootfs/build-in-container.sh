#!/usr/bin/env bash
#
# ./$0
# CONTAINER=docker ./$0
#

set -eu

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONTAINER=${CONTAINER:-}
IMAGE=kali-build/kali-wsl-rootfs
OPTS=()
SUDO=

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

## Output bold only if both stdout/stderr are opened on a terminal
if [ -t 1 ] && [ -t 2 ]; then
  b() { tput bold; echo -n "$@"; tput sgr0; }
else
  b() { echo "$@"; }
fi
## Last program in this script should use exec
vexec() { b "# $@"; echo; exec "$@"; }
vrun()  { b "# $@"; echo;      "$@"; }
fail() { echo "ERROR: $@"   1>&2; exit 1; }
warn() { echo "WARNING: $@" 1>&2; }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if [ -x "$( which podman )" ] && \
  ([ -z "${CONTAINER}" ] || [ "${CONTAINER}" == "podman" ]); then
  CONTAINER=podman

  ## We don't want stdout in the journal
  OPTS+=(--log-driver none)
elif [ -x "$( which docker )" ] && \
  ([ -z "${CONTAINER}" ] || [ "${CONTAINER}" == "docker" ]); then
  CONTAINER=docker
else
  fail "No container engine detected, aborting."
fi

## Permissions & security
## - MKNOD is default with Docker, not Podman (at time of writing!)
## - (Linux) security-opt / (macOS) SYS_ADMIN is for: mount -t proc proc /proc
##   Isn't a blocker, but highly recommended
##   Reduces warnings and allows for additional packages (closer to bare metal build)
OPTS+=(
  --cap-add=CHOWN
  --cap-add=DAC_OVERRIDE
  --cap-add=FOWNER
  --cap-add=MKNOD
  --cap-add=SETGID
  --cap-add=SETUID
  --cap-add=SYS_ADMIN
  --cap-add=SYS_CHROOT
  --cap-drop=ALL

  --security-opt label=disable
  --security-opt apparmor=unconfined
)

## If stdin is an option, use tty
if [ -t 0 ]; then
  OPTS+=(
    --interactive
    --tty
  )
fi

OPTS+=(
  --rm
  --network host
  --volume "$( pwd ):/recipes" --workdir /recipes
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

function build_container() {
  if ! ${SUDO} "${CONTAINER}" inspect --type image "${IMAGE}" >/dev/null 2>&1; then
    vrun ${SUDO} "${CONTAINER}" build --tag "${IMAGE}" .
    echo
  fi
}
build_container

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if [ "${CONTAINER}" == "podman" ]; then
  ## Need to be "rootful" as "--privileged" and "--cap-add=all" gives:
  ##   E: Cannot install into target '/tmp/tmp.XXXXXXXXXX' mounted with noexec or nodev
  uid_map=$( "${CONTAINER}" run "${IMAGE}" cat /proc/self/uid_map )
  if ! echo "${uid_map}" | grep -wq '0 .* 0'; then
    warn "${CONTAINER} is not rootful (currently rootless)"
    ## No 100% on v4.1 but not an option Debian 11/Podman 3.0.1 & Ubuntu 22.10/Podman 3.4.4
    warn "Trying 'sudo', but if ${CONTAINER} supports it (v4.1+), try: $ podman machine set --rootful=true"
    ## macOS and Linux behave a little different here
    ## Error:
    ##   E: debootstrap can only run as root
    sleep 2s
    SUDO="sudo"
  fi
  build_container
fi

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

vexec ${SUDO} "${CONTAINER}" run "${OPTS[@]}" "${IMAGE}" ./build.sh "$@"
