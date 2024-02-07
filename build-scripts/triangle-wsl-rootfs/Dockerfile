## REF: https://hub.docker.com/_/debian
FROM docker.io/debian:stable-slim

RUN \
  apt-get --quiet update && \
  ## Install Kali archive keyring
  env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install --no-install-recommends \
    wget ca-certificates && \
  KEYRING_PKG_URL=$( wget -nv -O - \
      https://http.kali.org/kali/dists/kali-rolling/main/binary-amd64/Packages.gz \
        | gzip -dc \
        | grep "^Filename: .*/kali-archive-keyring_.*_all.deb" \
        | head -n 1 \
        | awk '{print $2}' ) && \
  wget -nv "https://http.kali.org/kali/${KEYRING_PKG_URL}" && \
  dpkg -i kali-archive-keyring_*_all.deb && \
  rm -v kali-archive-keyring_*_all.deb && \
  apt-get --quiet --yes purge wget ca-certificates && \
  ## Install packages
  ## REF: ./README.md
  env DEBIAN_FRONTEND=noninteractive apt-get --quiet --yes install --no-install-recommends \
    debootstrap qemu-user-static qemu-system-arm && \
  ## Clean up
  apt-get --quiet --yes --purge autoremove && \
  apt-get --quiet --yes clean
