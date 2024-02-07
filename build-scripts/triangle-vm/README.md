# Kali VM image builder

This is the build script to create the Kali Linux [Virtual Machine (VM)](https://www.kali.org/docs/virtualization/) images.

Currently there are two build methods are possible:

- `build.sh` - build straight from your machine
- `build-in-container.sh` - build from within a container (Docker or Podman)

Either way, the build actually happens from within a virtual machine that is created on-the-fly by the build tool [debos](https://github.com/go-debos/debos).
_Debos uses [fakemachine](https://github.com/go-debos/fakemachine) under the hood, which in turn relies on QEMU/KVM._

## Prerequisites

Make sure that the git repository is cloned locally:

```console
$ sudo apt install -y git
$ git clone https://gitlab.com/kalilinux/build-scripts/kali-vm.git
$ cd kali-vm/
```

### User setup

Due to the requirements of QEMU/KVM, you must be part of the `kvm` group.
You can check by doing:

```console
$ # Not apart of the group
$ grep kvm /etc/group
kvm:x:104:
$
$ # In the group
$ grep kvm /etc/group
kvm:x:104:kali
```

If your username does not appear in the line returned, it means that you are not in the group, and you must add yourself to the `kvm` group:

```console
$ sudo adduser $USER kvm
```

Then **log out and log back in** for the change to take effect.

### Build from the host

If building straight from your machine, using `build.sh`, you will need to install `debos`:

<!--
  This should match what is in: ./Dockerfile
  There are a few recommended packages which are also required: bmap-tools linux-image-amd64 parted systemd-resolved xz-utils
-->

```console
$ sudo apt install -y debos p7zip qemu-utils zerofree
```

Then use the script `build.sh` to build an VM image directly on your machine.

### Build from within a container

If you prefer to build from within a container, you will need to install and configure either `docker` or `podman` on your machine.
Then use the script `build-in-container.sh` to build a image.

`build-in-container.sh` is simply a wrapper on top of `build.sh`.
It will detect which OCI-compliant container engine to use, takes care of creating the [container image](Dockerfile) if missing, and then finally it starts the container to perform the build from within.

`docker` requires the user to be added to the Docker group, just like the above with KVM, or using the root account (e.g. `$ sudo ./build-in-container.sh`).
`podman` has been tested with both as rootful (e.g. `$ sudo ./build-in-container.sh`) and rootless (e.g. `$ ./build-in-container.sh`).

## Building an image

Use either `build.sh` or `build-in-container.sh`, at your preference.
From this point we will use `build.sh` for brevity.

### Examples

The best starting point, as always, is the usage message:

```console
$ ./build.sh -h
Usage: build.sh <options> [-- <debos options>]

Build a Kali Linux VM image

Build options:
  -a ARCH     Build an image for this architecture, default: amd64
              Supported values: amd64 i386
  -b BRANCH   Kali branch used to build the image, default: kali-rolling
              Supported values: kali-dev kali-last-snapshot kali-rolling
  -f FORMAT   Format to export the image to, default depends on the VARIANT
              Supported values: hyperv ova ovf qemu raw virtualbox vmware
  -k          Keep raw disk image and other intermediary build artifacts
  -m MIRROR   Mirror used to build the image, default: http://http.kali.org/kali
  -r ROOTFS   rootfs to use to build the image, default: none
  -s SIZE     Size of the disk image in GB, default: 86
  -v VARIANT  Variant of image to build (see below for details), default: generic
              Supported values: generic hyperv qemu rootfs virtualbox vmware
  -x VERSION  What to name the image release as, default: rolling
  -z          Zip images and metadata files after the build

Customization options:
  -D DESKTOP  Desktop environment installed in the image, default: xfce
              Supported values: e17 gnome i3 kde lxde mate xfce none
  -L LOCALE   Set locale, default: en_US.UTF-8
  -P PACKAGES Install extra packages (comma/space separated list)
  -T TOOLSET  The selection of tools to include in the image, default: default
              Supported values: default everything headless large none
  -U USERPASS Username and password, separated by a colon, default: kali:kali
  -Z TIMEZONE Set timezone, default: America/New_York

The different variants of images are:
  generic     Image with all virtualization support pre-installed, default format: raw
  hyperv      Image pre-configured for Hyper-V "Enhanced Session Mode", default format: hyperv
  qemu        Image with QEMU and SPICE guest agents pre-installed, default format: qemu
  rootfs      Not an image, a root filesystem (no bootloader/kernel), packed in a .tar.gz
  virtualbox  Image with VirtualBox guest utilities pre-installed, default format: virtualbox
  vmware      Image with Open VM Tools pre-installed, default format: vmware

The different formats are:
  hyperv      VHDX disk image, powershell install scripts
  ova         streamOptimized VMDK disk image, OVF metadata file, packed in a OVA archive
  ovf         monolithicSparse VMDK disk image, OVF metadata file
  qemu        QCOW2 disk image, no metadata
  raw         sparse disk image, no metadata
  virtualbox  VDI disk image, .vbox metadata file
  vmware      2GbMaxExtentSparse VMDK disk image, VMX metadata file

Supported environment variables:
  http_proxy  HTTP proxy URL, refer to the README.md for more details

Most useful debos options:
  --artifactdir DIR   Set artifact directory, default: images
  --memory, -m  SIZE  Limit amount of memory to build VM in GB, default: 4G
  --scratchsize SIZE  Limit amount of HDD to build VM in GB, default: 45G
  --debug-shell       Get a shell on the VM
  --help, -h          See the complete list of options for debos

Refer to the README.md for examples
```

- - -

The default options will build a [Kali rolling](https://www.kali.org/docs/general-use/kali-branches/) image, [default desktop](https://www.kali.org/docs/general-use/switching-desktop-environments/) and [default toolset](https://www.kali.org/docs/general-use/metapackages/) for AMD64 architecture.

This is a raw disk image, i.e. a plain binary image of the disk (which can be started with [QEMU](https://www.kali.org/docs/virtualization/install-qemu-guest-vm/)).

Example:

```console
$ ./build.sh
```

- - -

To build a Kali Linux image tailored for VMware.
It means that it comes with the Open VM Tools pre-installed, and the image produced is ready to be imported "as is" in VMware.

Also, we are going to build it from the [last stable release](https://www.kali.org/docs/general-use/kali-branches/) of Kali, and we will using GNOME as the desktop environment, rather than the usual default Xfce:

```console
./build.sh -v vmware -b kali-last-snapshot -D gnome
```

- - -

To build a Kali Linux image designed for VirtualBox.
It comes with the VirtualBox guest utilities pre-installed, and the image can be imported "as is" in VirtualBox.

Moreover, we want a 150 GB virtual disk, and we will install the "everything" tool selection:

```console
./build.sh -v virtualbox -s 150 -S everything
```

- - -

To build a lightweight Kali image, which has no desktop environment and no default toolset.
This is a generic image, it comes with support for most VM engines out there.
We will export it to the OVA format, suitable for both VMware and VirtualBox.

You can install additional packages with the `-P` option.
Either use the option several times (e.g. `-P pkg1 -P pkg2 ...`), or give a comma/space separated value (e.g. `-P "pkg1,pkg2, pkg3 pkg4"`), or a mix of both.
Let's also install the package `metasploit-framework`:

```console
./build.sh -v generic -f ova -D headless -P metasploit-framework
```

- - -

To set the `locale`, use the option `-L`.
Pick a value in the 1st column of `/usr/share/i18n/SUPPORTED`, or check what's configured on your system with `grep -v ^# /etc/locale.gen`, or simply `echo $LANG`.
There is also a shortcut of `-L same` to match the host system.

To set the `timezone`, use the option `-Z`.
Look into `/usr/share/zoneinfo` and pick a directory and a sub-directory.
In doubt, run `tzselect` to guide you, or look at what's configured on your system with `realpath /etc/localtime`.
There is also a shortcut of `-Z same` to match the host system.

To set the name and password for the unprivileged user, use the option `-U`.
The value is a single string and the `:` is used to separate the username from the password.

Here we will build a Kali image, and configure it to mimic the host system: same locale and same timezone and same username (with the password of `password`):

```console
./build.sh -L same -Z same -U $USER:password
```

### Variants and formats

Different variants of image can be built, depending on what VM engine you want to run the Kali image in.
The VARIANT mostly defines what extra package gets installed into the image, to add support for a particular VM engine.
Then the FORMAT defines what format for the virtual disk, and what additional metadata files to produce.

If unset, the format (option `-f`) is automatically set according to the variant (option `-v`).
Not every combination of variant and format make sense, so the table below tries to summarize the most common combinations.

| variant    | format     | disk format             | metadata | pack |
| ---------- | ---------- | ----------------------- | -------- | ---- |
| generic    | raw        |       raw (sparse file) |     none |      |
| generic    | ova        |    streamOptimized VMDK |      OVF |  OVA |
| generic    | ovf        |   monolithicSparse VMDK |      OVF |      |
| qemu       | qemu       |                   QCOW2 |     none |      |
| virtualbox | virtualbox |                     VDI |     VBOX |      |
| vmware     | vmware     | 2GbMaxExtentSparse VMDK |      VMX |      |

The `generic` images come with virtualization support packages pre-installed for QEMU, VirtualBox and VMware, hence the name "generic".
While other images, that target a specific VM engine, only come with support for this particular virtualization engine.

Only the format `ova` defines a container: the result of the build is a `.ova` file, which is simply a tar archive.
For other formats, the build produce separate files.
They can be bundled together in a 7z archive with the option `-z`.

There is also a `rootfs` type: this is not an image.
It's simply a Kali Linux root filesystem tree, without the kernel and the bootloader, and packed in a `.tar.gz` archive.
The main use-case is to reuse it as input to build an OS image, and it's not meant to be used outside of the build system.

### Caching proxy configuration

When building OS images, it is useful to have a caching mechanism in place, to avoid having to download all the packages from the Internet, again and again.
To this effect, the build script attempts to detect known caching proxies that would be running on the local host, such as `apt-cacher-ng`, `approx` and `squid-deb-proxy`.
Alternatively, you can setup a [local mirror](https://www.kali.org/docs/community/setting-up-a-kali-linux-mirror/).

To override this detection, you can export the environment variable `http_proxy` yourself.
However, you should remember that the build happens within a QEMU Virtual Machine, therefore `localhost` in the build environment refers to the VM, not to the host.
If you want to reach the host from the VM, you probably want to use `http://10.0.2.2`.

For example, if you want to use a proxy that is running on your machine on the port 9876, use: `export http_proxy=10.0.2.2:9876`.
If you want to make sure that no proxy is used: `export http_proxy= ./build.sh [...]`.

Also refer to <https://github.com/go-debos/debos#environment-variables> for more details.

### Building and reusing a rootfs

It's possible to break the build in two steps.
You can first build a rootfs with `./build.sh -v rootfs`, and then build an image based on this rootfs with `./build.sh -r ROOTFS_NAME.tar.gz`.
It makes sense if you plan to build several image types, for example.

## Troubleshooting the build

### Not enough memory

When the scratch area gets full (i.e. the `--scratchsize` value is too low), the build might fail with this kind of error messages:

```console
[...]: failed to write (No space left on device)
[...]: Cannot write: No space left on device
```

Solution: bump the value of `--scratchsize`.
You can pass arguments to debos after the special character `--`, so if you need for example 50G, you can do `./build.sh [...] -- --scratchsize=50G`.

### Get a shell in the VM when the build fails

When debugging build failures, it's convenient to be dropped in a shell within the VM where the build takes place.
This is possible by giving the option `--debug-shell` to debos: `./build.sh [...] -- --debug-shell`.

## Troubleshooting at runtime

### ovf not compatible with VMware ESXI

This is a known issue, refer to <https://gitlab.com/kalilinux/build-scripts/kali-vm/-/issues/25#note_1301070132> for a workaround.
