# Gather details about Mirrorbits instances in the wild

Run as such:

```
./run.py mirrorbits.yaml
```

It can be useful to do a run for only one instance, eg:

```
./run.py -i gimp mirrorbits.yaml
```

To also get the number of files on the mirror, we need to enable the rsync
listing. Since it takes a while to run, we'd better also save the complete
output into a directory:

```
./run.py -i gimp -o out --rsync mirrorbits.yaml
```

There are more settings available, but not exposed via the command-line, so
have a look at the script and modify what needs be.

## Discover mirrorbits instances

- mirrorbits's [README.md](https://github.com/etix/mirrorbits/blob/master/README.md#is-it-production-ready)
- HTTP Response Header: `Server: Mirrorbits/vX.Y.Z`
  - [shodan.io](https://www.shodan.io/search?query=mirrorbits)
  - [censys.io: `services.http.response.headers.server:mirrorbits`](https://search.censys.io/search?resource=hosts&q=services.http.response.headers.server%3Amirrorbits)
- HTTP URL: `?mirrorstats` / `?mirrorlist`
  - [Google: `mirrorbits inurl:"?mirrorstats"`](https://www.google.com/search?q=mirrorbits+inurl%3A%22%3Fmirrorstats%22)
  - [Google: `mirrorbits inurl:"?mirrorlist"`](https://www.google.com/search?q=mirrorbits+inurl%3A%22%mirrorlist%22)
