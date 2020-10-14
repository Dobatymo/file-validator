# file-validate

## What is it?

A commandline program to generate xml reports about the validity of files. It scans directories and tests every file for errors. This is useful to find corrupt files on the hdd.

## How do I use it?

- Install Python
- `pip install -r requirements.txt`
- `validator.py --help`

## Dependencies

* main program:
    * none
* plugins:
    * Archives: unrar and 7z executable, set path in plugin
    * Images: Python Imaging Library (PIL)
    * PDF: python library 'pyPdf'
    * Videos: ffmpeg executable, set path in plugin
    * FLAC: flac executable, set path in plugin

## How does it work?

It loads plugins which handle one or more file extensions. Then for every file the right plugin is used to validate it and output the results to a xml file.

## It doesn't support file type .xxx

Plugins can be written by everybody. For an example of a trivial plugin see 'plugins/txt.py'.
