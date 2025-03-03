# dir_sync

A directory synchronization tool.

## Overview

This tool synchronizes two directories at specified intervals. Copying new files from the source directory to the replica directory, deletes files in the replica directory that are not in the source directory, and updates files in the replica directory that are different from the source directory.

## Usage

To use this tool, simply run the `main.py` script with the following arguments:

* `-s` or `--source`: the path to the source directory
* `-r` or `--replica`: the path to the replica directory
* `-t` or `--time`: the synchronization interval in seconds
* `-l` or `--log`: the path to the log file

Example:
```bash
python main.py -s /path/to/source -r /path/to/replica -t 60 -l /path/to/log.txt
