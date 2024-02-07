## REF: https://hub.docker.com/r/kalilinux/kali-rolling
FROM docker.io/kalilinux/kali-rolling

RUN apt-get --quiet update && \
## Install packages
## REF: ./README.md
  env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install --no-install-recommends \
    bmap-tools debos dosfstools linux-image-amd64 p7zip parted qemu-utils systemd-resolved xz-utils zerofree && \
## Clean up
  apt-get --quiet --yes --purge autoremove && \
  apt-get --quiet --yes clean
