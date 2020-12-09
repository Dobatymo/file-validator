# file-validate

## What is it?

A commandline program to generate xml reports about the validity of files. It scans directories and tests every file for errors. This is useful to find corrupt/broken files on the hdd.

## How do I use it?

- Install Python 3.8+
- `py -m pip install -r requirements.txt`
- `py -m pip install -r plugins/requirements.txt`
- `py validator.py --help`

## CLI usage
``` usage: validator.py [-h] [-d REPORTDIR] [-x XSLFILE] [-r] [-v] [-i EXT [EXT ...]] [--relative] [--resume RESUME]
                    DIRECTORY [DIRECTORY ...]

FileValidator

positional arguments:
  DIRECTORY             directories to create report for

optional arguments:
  -h, --help            show this help message and exit
  -d REPORTDIR, --reportdir REPORTDIR
                        set output directory for reports (default: reports)
  -x XSLFILE, --xsl XSLFILE
                        set XSL style sheet file (default: report.xsl)
  -r, --recursive       scan directories recursively (default: False)
  -v, --verbose         output debug info (default: False)
  -i EXT [EXT ...], --ignore EXT [EXT ...]
                        extensions to ignore (default: [])
  --relative            Output relative paths (default: False)
  --resume RESUME       Resume validation using a previous XML report (default: None)
```

## Example
- `py validator.py -r "C:\PUBLIC"`

## Non-Python dependencies

* Plugins:
  * Archives: unrar and 7z executable, set path in plugin
  * Videos: ffmpeg executable, set path in plugin
  * FLAC: flac executable, set path in plugin

## How does it work?

It loads plugins which handle one or more file extensions. Then for every file the right plugin is used to validate it and output the results to a xml file.

## It doesn't support file type .xxx

Plugins can be written by everybody. For an example of a trivial plugin see `plugins/txt.py`.
