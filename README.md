# ReAr

[![PyPI version](https://img.shields.io/pypi/v/rear.svg)](https://pypi.org/project/rear)

Remote Archiver: safely collect output files into archives on network filesystem

Replacement of `open()` for scenario where multiple processes generate lots of (log) files on a network filesystem. ReAr redirects the writes to Zip files to reduce the stress on the filesystem and to keep things organized. Writing to archive is chunked and staged to avoid single point of failure.

```python
# On each worker:
async with rear_fs("/path/to/archive_base"):
    with rear_open("ar.zip/relpath/to/file", 'w+b') as f: # open a read-write buffer ...
    #with rear_pickup("/path/to/temp-file", "ar.zip/relpath/to/file"): # ... or pick up a file created by others
        f.write(b"...")
    # The file is written to a tmp archive on closing.
    # It will then be moved and eventually stored as `relpath/to/file` in zip file `/path/to/archive_base/ar.zip`.
```

To avoid concurrent write, each worker writes to a temporary Zip file, and they create a new one every 5 minutes. Run a scavenger to collect the files in the temporary archives into the final archives:

```python
# On your main process:
async with scavengerd("/path/to/archive_base"):
    ...
```

```bash
# ... or to do it manually
while :; do
    rear-scavenger -d /path/to/archive_base
    sleep 5m
done
```

### FAQ

#### What happens if a worker instance crashes?

Its current temporary archive will end up missing the central directory list as it is not properly closed. Scavenger will try to recover the files as much as possible (with `zip -FF`).

#### How does the scavenger works?

Multiple processes cannot write to one Zip file at the same time, so each first deposit the files to individual temporary Zip files and record where those files should be saved eventually. When a temporary Zip file is closed (after the process exit or after 5 minutes), Scavenger copies all files to their destination Zip files. Scavenger does not need to watch for incoming files actively since it can organize them any time after they are saved to the temporary Zip files. It is also safe to run multiple Scavenger instances at any time: it will check if it is necessary before performing any action.

