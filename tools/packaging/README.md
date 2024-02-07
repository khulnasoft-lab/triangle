**Kali's Helper Packagers Packaging Tools**

_Helper scripts, mixture of shell & python code, to help (semi-)automate Kali's huge set of [projects](https://gitlab.com/kalilinux/packages) for [packages](https://pkg.kali.org/), both local repositories & remote GitLab.com SaaS activities._

Other related projects:

- Britney - Handling package migration
  - Live: [repo.kali.org/britney/](http://repo.kali.org/britney/)
  - Code: [gitlab.com/kalilinux/tools/britney2](https://gitlab.com/kalilinux/tools/britney2)
- Upstream Watch - Package upstream notification
  - Live: [kalilinux.gitlab.io/tools/upstream-watch/](https://kalilinux.gitlab.io/tools/upstream-watch/)
  - Code: [gitlab.com/kalilinux/tools/upstream-watch](https://gitlab.com/kalilinux/tools/upstream-watch)

Other useful links:

- Kali AutoPkgTest - Automatic Package Testing using `debci`
  - Live: [autopkgtest.kali.org](https://autopkgtest.kali.org/)
- Kali Buildd - autobuilders daemon log output
  - Live: [repo.kali.org/build-logs/](https://repo.kali.org/build-logs/)
  - Live: [buildd-amd64.kali.org/logs/](https://buildd-amd64.kali.org/logs/)
- Kali Janitor - Package automation
  - Live: [janitor.kali.org](https://janitor.kali.org/)
  - _Long term goal would be to offload some of these scripts into campaigns there_
- Kali Package Tracker - Package history
  - Live: [pkg.kali.org](https://pkg.kali.org/)

[[_TOC_]]

- - -

## Local setup

A quick way of getting set-up on a Debian-based OS:

```console
$ sudo apt update
[...]
$ sudo apt install --no-install-recommends --yes \
    curl ca-certificates jq \
    devscripts libgitlab-api-v4-perl \
    git \
    mr git-buildpackage openssh-client \
    python3-minimal python3-gitlab python3-yaml
[...]
$ git clone https://gitlab.com/kalilinux/tools/packaging.git ~/kali/tools/
[...]
```

### API/Token

When some of the scripts interact with GitLab they will alter upstream thus they require authentication!
For them to work, you will need to setup a "Personal Access Token" granting access to GitLab.com's API.
You can do that here: <https://gitlab.com/-/profile/personal_access_tokens>

When you have your key, store it `./.gitlab-token`, in the root of this folder, with this command _(replace `XXX` with the real token)_:

```console
$ echo "SALSA_TOKEN='XXX'" > ./.gitlab-token
```

_This is different to adding a [SSH key](https://gitlab.com/-/profile/keys) and/or [GPG key](https://gitlab.com/-/profile/gpg_keys) to your GitLab.com profile - something we do recommend doing!_

## `ls ./bin/`

This is a brief overview of the files found in `./bin/`. Check their source for more details.

### `./bin/archive-gitlab`: Disable an unused git repository.

To archive obsolete project(s) in the [Kali's packages sub-group](https://gitlab.com/kalilinux/packages):

```console
$ ./bin/archive-gitlab apt2 ruby-librex
[+] apt2 archived ~ https://gitlab.com/kalilinux/packages/apt2
[+] ruby-librex archived ~ https://gitlab.com/kalilinux/packages/ruby-librex
[+] Done
$
```

**NOTE:** After having used that command you should probably update mrconfig's repositories list with: `./bin/update-mrconfig`

### `./bin/archive-local`: Move local packages that are archived remotely.

Over time, projects will be archived for various reasons.

If you wish to move any local repositories to a different location (e.g. `~/kali/packages/` -> `~/kali/archived/`):

```console
$ ./bin/archive-local ~/kali/packages/ ~/kali/archived/
[>] Comparing '/home/user/kali/packages/.mrconfig' with 'ls /home/user/kali/packages/*' to see if any projects which may have been archived
[>] Archive '/home/user/kali/packages/apt2' to '/home/user/kali/archived/apt2'
[?] Proceed? [Y/n] y
renamed '/home/user/kali/packages/apt2' -> '/home/user/kali/archived/apt2'
[...]
[+] Done
$
```

### `./bin/branchprotection-gitlab`: Reset branch protection

This will reset any branch protection, to allow developers to push and merge:

```console
$ ./bin/branchprotection-gitlab --all
[i] Fetching all projects
[i] Total: 637 projects
[>] Setting branch protection for 0trace ~ https://gitlab.com/kalilinux/packages/0trace
[...]

[+] Done
$
```

- - -

Otherwise, you can select certain projects:

```console
$ ./bin/branchprotection-gitlab 0trace zaproxy
[>] Setting branch protection for 0trace ~ https://gitlab.com/kalilinux/packages/0trace
salsa info: Project 0trace => kalilinux/packages/0trace
salsa info: kalilinux/packages/0trace id is 11903448
salsa info: Project 0trace => kalilinux/packages/0trace
salsa info: kalilinux/packages/0trace id is 11903448

[>] Setting branch protection for zaproxy ~ https://gitlab.com/kalilinux/packages/zaproxy
[...]

[+] Done
$
```

### `./bin/build-gitlab`: Run a package's scheduled pipeline

This will run each package's scheduled pipeline task of "Monthly Build".

If this is run under GitLab's CI, it will use the variable `$CI_JOB_TIMEOUT`, to wait between runs, otherwise, will just skip.

```console
$ ./bin/build-gitlab --all
[i] Loading GitLab API Key (File: .gitlab-token)
[i] Found system variable: $SALSA_TOKEN
[i] Found (sub-)group: https://gitlab.com/kalilinux/packages (ID: 5034987)
[i] Fetching all projects
[i] Found 637 projects (https://gitlab.com/kalilinux/packages)
[-] Missing $CI_JOB_TIMEOUT
[+] (1/637) Running 'Monthly Build' for 0trace (ID: 11903448)
[i]       Sleeping: 0 seconds
[...]
[+] Done
$
```

### `./bin/clone-gitlab`: Checkout all repositories in a dedicated directory

To checkout all of Kali's packages at once:

```console
$ ./bin/clone-gitlab ~/kali/packages
mkdir: created directory '/home/user/kali'
mkdir: created directory '/home/user/kali/packages/'
[>] To easily clone all repositories, create: /home/user/kali/packages/.mrconfig
[?] Proceed? [Y/n]
'/mnt/packaging/mrconfig' -> '/home/user/kali/packages/.mrconfig'
[>] Force clone all repositories into: /home/user/kali/packages
[?] Proceed? [Y/n]
mr checkout: /home/user/kali/packages/0trace
Cloning into '0trace'...
gbp:info: Cloning from 'git@gitlab.com:kalilinux/packages/dpkg.git'
[...]
mr checkout: finished (634 ok; 0 failed)
$
```

_This way you pull down multiple branches at once._

### `./bin/configure-gitlab`: Configure remote GitLab packaging repositories

This makes use of the GitLab's API to set-up various items, such as:

- Configure the CI path to `debian/kali-ci.yml`
- Enable merge requests and issues feature
- Ensure `kali/master` is the default branch
- Setup email notifications
- Standardize the project's description

This will use the contents from: `./salsa.d/packages.conf`

**NOTE:** Newer versions of `devscripts` (aka newer Debian) will have more options.

To verify all repositories from the [packages sub-group](https://gitlab.com/kalilinux/packages) and reconfigure those which are not consistent with our rules:

```console
$ ./bin/configure-gitlab --all
[i] Fetching all projects
[i] Total: 637 projects
[...]
1 packages misconfigured, update them ? (Y/n) y
salsa warn: You're not member of this group
salsa info: Project rzpipe => kalilinux/packages/rzpipe
salsa info: Configuring rzpipe
salsa warn: Deleting old email-on-push (redirected to devel+git@kali.org dispatch@pkg.kali.org)
salsa info: Email-on-push hook added to project 45508309 (recipients: devel+git@kali.org dispatch@pkg.kali.org)
salsa info: Head already renamed for rzpipe
salsa info: Project rzpipe updated
[+] Done
$
```

- - -

Otherwise, to configure just a selected amount of projects:

```console
$ ./bin/configure-gitlab 0trace zaproxy
salsa info: Project 0trace => kalilinux/packages/0trace
salsa info: kalilinux/packages/0trace id is 11903448
salsa info: Project zaproxy => kalilinux/packages/zaproxy
salsa info: kalilinux/packages/zaproxy id is 11904434
salsa info: 0trace: OK
salsa info: zaproxy: OK
[+] Done
$
```

### `./bin/configure-local`: Apply common changes for all Kali source packages

This will apply many Kali specific customizations to the local git repository, such as:

- Adding/updating `debian/gbp.conf`
- Adding/updating `debian/kali-ci.yaml`
- Updating `Vcs-Git` and `Vcs-Browser` fields
- Updating the `Maintainer` field to the official Kali value

This will use the contents from: `./configure-local.d/`

There are a few different ways to run this, such as:

- Assuming that `$PACKAGING_DIR` contains the path to this git repository, once inside a package directory, run `$PACKAGING_DIR/bin/configure-local`
- Passing path(s) of the package directory

There are a few command line arguments when using this:

```plaintext
--push (default) / --no-push     - Submit changes back to GitLab's repository
--commit / --no-commit (default) - Stage or commit changes
--quiet / --verbose              - Make more or less output than standard
```

- - -

Below is an explanation of running against two packages (with more output shown):

```console
$ ./bin/configure-local ~/kali/packages/{0trace,zaproxy} --verbose
[>] Doing: /home/user/kali/packages/0trace/
    Applying: 10-control.sh
    Applying: 10-kali-ci.sh
** NEW CHANGE: Add GitLab's CI configuration file **

commit c5d4c290f1b82bfa29862a93361f2b593f898266 (HEAD -> kali/master)
Author: Your Name <you@example.com>
Date:   Sat Aug 12 20:02:58 2023 +0000

    Add GitLab's CI configuration file

diff --git a/debian/kali-ci.yml b/debian/kali-ci.yml
new file mode 100644
index 0000000..058e396
--- /dev/null
+++ b/debian/kali-ci.yml
@@ -0,0 +1,2 @@
+include:
+  - https://gitlab.com/kalilinux/tools/kali-ci-pipeline/raw/master/recipes/kali.yml

    Applying: 20-gbp.sh
[>] Doing: /home/user/kali/packages/zaproxy
    Applying: 10-control.sh
    Applying: 10-kali-ci.sh
    Applying: 20-gbp.sh
[+] Done
$
````

- - -

Below is an example of looping every package in `~/kali/packages/`, using some bash:

```console
$ ls -1 ~/kali/packages/ \
  | while read -r package; do
    cd "~/kali/packages/${package}/";
    out=$( ~/kali/tools/bin/configure-local );
    [ -n "${out}" ] && echo -e "${package}\n${out}\n";
  done
[...]
$
```

### `./bin/file-issues`: Create many GitLab issues

If you have to file the same issue against a large number of projects, you can use this:

```console
$ ./bin/file-issues 0trace ./file-issues.d/python2-eol.yml
Searching for: 0trace should get rid of Python 2 and use Python 3 only
[i] Found issue: https://gitlab.com/kalilinux/packages/0trace/-/issues/3
[i] Found link: https://gitlab.com/kalilinux/internal/roadmap/issues/27
[+] Created link between: https://gitlab.com/kalilinux/packages/0trace/-/issues/3 & https://gitlab.com/kalilinux/internal/roadmap/-/issues/27
$
```

This will use the contents from: `./file-issues.d/`

- - -

Otherwise, to run on a selected amount of projects (as well as only seeing what would happen without running everything but the build itself):

```console
$ ./bin/build-gitlab 0trace zaproxy --dry-run
[i] Loading GitLab API Key (File: .gitlab-token)
[i] Found system variable: $SALSA_TOKEN
[i] Found (sub-)group: https://gitlab.com/kalilinux/packages (ID: 5034987)
[i] Found 2 projects (https://gitlab.com/kalilinux/packages)
[-] Missing $CI_JOB_TIMEOUT
[+] (1/2) Running 'Monthly Build' for 0trace (ID: 11903448)
[i]       Sleeping: 0 seconds
[i]       DRY RUN
[+] (2/2) Running 'Monthly Build' for zaproxy (ID: 11904434)
[i]       Sleeping: 0 seconds
[i]       DRY RUN
[+] Done
$
```

### `./bin/gitlab-overview`: Create HTML overview of CI status

This will make a [very quick & dirty "overview"](https://kalilinux.gitlab.io/tools/packaging) of our [kali-ci-pipeline](https://gitlab.com/kalilinux/tools/kali-ci-pipeline/) status:

```console
$ ./bin/gitlab-overview
[>]    Pulling: https://gitlab.com/kalilinux/packages (5034987)
0trace: success
[...]
[i] success : 585
[i] failed  : 36
[i] disabled: 12
[i] running : 0
[i] unknown : 2
[+] Done
$
$ file ./report.html
./report.html: HTML document, ASCII text
$
```

If successful there will be a single file create `./report.html`.

### `./bin/retry-gitlab`: (Re-)run package's scheduled pipeline

This will run a package's pipeline if its last status was not successful:

```console
$ ./bin/retry-gitlab --all
[i] Loading GitLab API Key (File: .gitlab-token)
[i] Found system variable: $SALSA_TOKEN
[i] Found (sub-)group: https://gitlab.com/kalilinux/packages (ID: 5034987)
[i] Fetching all projects
[i] Found 637 projects (https://gitlab.com/kalilinux/packages)
[i] Re-running aioconsole (22503415)'s failed job: build ~ https://gitlab.com/kalilinux/packages/aioconsole/-/jobs/4826619222
[...]
[+] Re-ran 263 unsuccessful jobs (36 broken pipelines)
[+] Done
$
```

- - -

Otherwise, you can select certain projects to run (if these were not successful):

```console
$ ./bin/retry-gitlab 0trace zaproxy --quiet
[i] Loading GitLab API Key (File: .gitlab-token)
[i] Found system variable: $SALSA_TOKEN
[i] Found (sub-)group: https://gitlab.com/kalilinux/packages (ID: 5034987)
[i] Found 2 projects (https://gitlab.com/kalilinux/packages)
[+] Re-ran 0 unsuccessful jobs (0 broken pipelines)
[+] Done
$
```


### `./bin/update-mrconfig`: Update known repos

We track all public repositories in [Kali's packages sub-group](https://gitlab.com/kalilinux/packages) in `./mrconfig`. To keep it up-to-date:

```console
$ ./bin/update-mrconfig
[i] Found (sub-)group: https://gitlab.com/kalilinux/packages (ID: 5034987)
[i] Fetching all projects
[i] Found 637 projects (https://gitlab.com/kalilinux/packages)
[+] Done
$
```

If you have not added an [SSH key](https://gitlab.com/-/profile/gpg_keys) to GitLab, you may wish to check out via HTTPS instead as this is unauthenticated. You can switch to this by doing `./bin/update-mrconfig --https`.

## `cat ./.gitlab-ci.yml`

We are using GitLab.com's Continuous Integration (CI), [to run various tasks at various times](./.gitlab-ci.yml).

All scheduled tasks happen at [00:00 UTC](https://time.is/UTC), which includes:

- Daily:
  - `./bin/configure-gitlab`
  - `./bin/gitlab-overview`: Output is on a GitLab page, which can be found here: [kalilinux.gitlab.io/tools/packaging/](https://kalilinux.gitlab.io/tools/packaging/)
  - `./bin/update-mrconfig`
- Monthly:
  - `./bin/build-gitlab`: On the last day of each month
<!--
- Fortnightly:
  `./bin/retry-gitlab`: Every 2nd Monday of the month
-->
