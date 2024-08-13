# file-validator

## What is it?

A command-line program to generate XML (or jsonlines) reports about the validity of files. It scans directories and tests every file for errors. This is useful to find corrupt/broken files on the HDD.

## How do I use it?

- Install Python 3.8+
- `py -m pip install .` or `py -m pip install .[html,images,orc,parquet,pdf,xml]` (including all plugin dependencies)
- `py -m filevalidator.validator --help`

## CLI usage
```
usage: validator.py [-h] [-d REPORTDIR] [-x XSLFILE] [-r] [-v] [--only EXT [EXT ...]] [-i EXT [EXT ...]] [--relative]
                    [--recall] [--resume RESUME] [--out {xml,json,stdout}]
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
  --only EXT [EXT ...]  only include these extensions (default: None)
  -i EXT [EXT ...], --ignore EXT [EXT ...]
                        extensions to ignore (default: None)
  --relative            Output relative paths (default: False)
  --recall              Download files which are currently only available online (on OneDrive for example), otherwise
                        they are skipped. (default: False)
  --resume RESUME       Resume validation using a previous XML report (default: None)
  --out {xml,json,stdout}
                        Output method. xml: write to xml file, json: write to json file, stdout: simple format written
                        to stdout (default: xml)
```

## Example
- `py -m filevalidator.validator "C:\PUBLIC"`

## Non-Python dependencies

* Plugins:
  * Archives: rar and 7z executable, must be in path, or set path in plugin config
  * Videos: ffmpeg executable, must be in path, or set path in plugin config
  * FLAC: flac executable, must be in path, or set path in plugin config

Plugin configs are JSON files loaded from `C:\Users\<username>\AppData\Local\Dobatymo\file-validator\config` (on Windows). See `config-example` for examples JSON files.

## How does it work?

It loads plugins which handle one or more file extensions. Then for every file the right plugin is used to validate it and output the results to a XML or jsonlines file.

## It doesn't support file type .xxx

Plugins can be written by everybody. For an example of a trivial plugin see `filevalidator/plugins/txt.py`.
