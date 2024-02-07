# Check availability of files served by mirrorbits

Request a file every minute. We don't really download the file though, instead
we set the header `Accept: application/json` in the request, so that mirrorbits
replies with a JSON file that contains the result of the redirection algorithm.

Let that run long enough (i.e. a few days), then analyze and plot the result,
to see whether the file was available from all mirrors reliably.

<!-- REF: https://github.com/etix/mirrorbits/issues/85 -->

NOTE: This requires the mirrorbits instances to have JSON output mode enabled,
which is it by default.
This can be set in the mirrorbits configuration option: `OutputMode:`, using
either `auto` or `json`.

## Step by step

Configure your mirrorbits instance with:

```
OutputMode: auto
```

Start the script to query some files every minute, let it run long enough:

```
./query-every-minute.sh out \
    http://mirrorbits.example.org/README \
    http://mirrorbits.example.org/AnotherFile
```

Then process the data:

```
./analyze-json.py out/README > out/README.dat
./analyze-json.py out/AnotherFile > out/AnotherFile.dat
```

And finally, plot it:

```
./plot.sh out/README.dat
./plot.sh out/AnotherFile.dat
```
