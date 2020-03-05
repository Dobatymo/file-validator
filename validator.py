from __future__ import absolute_import, division, print_function, unicode_literals

from future.utils import viewitems

import os, os.path, logging
from datetime import datetime

from genutility.twothree.filesystem import fromfs, sbs
from genutility.json import read_json

from plug import Filetypes
from xmlreport import xmlreport
import plugins

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def scandir(top, rec, followlinks=False):
    def joiner(dir, dirlist):
        for d in dirlist:
            yield os.path.join(dir, d)

    walker = os.walk(top, followlinks=followlinks)

    dirpath, __, filenames = next(walker)
    for path in joiner(dirpath, filenames):
        yield path
    if not rec:
        return
    for dirpath, __, filenames in walker:
        for path in joiner(dirpath, filenames):
            yield path

def main(paths, report_dir, xslfile, recursive, verbose=False, ignore=None):
    # type: (Sequence[str], str, str, bool, bool, Optional[set]) -> None

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    for name in plugins.__all__:
        __import__("plugins." + name)

    for class_, extensions in viewitems(Filetypes.PLUGINS):
        logger.info("Loaded Filetype plugin %s for: %s", class_.__name__, ", ".join(extensions))

    validators = {}
    no_validators = ignore or set()

    filename = "report_{}.xml".format(datetime.now().isoformat(sbs("_")).replace(":", "."))
    with xmlreport(os.path.join(report_dir, filename), xslfile) as report:

        for dir in paths:
            for path in scandir(dir, rec=recursive):
                logger.debug(path)
                ext = os.path.splitext(path)[1][1:].lower()

                if ext in no_validators:
                    continue

                validator = None
                try:
                    validator = validators[ext]
                except KeyError:
                    for class_, extensions in viewitems(Filetypes.PLUGINS):
                        if ext in extensions:
                            try:
                                config = read_json("config/{}.json".format(class_.__name__))
                            except IOError:
                                logger.info("Could not find config for '%s'", class_.__name__)
                                config = {}
                            except ValueError:
                                logger.exception("Could not load config for '%s'", class_.__name__)
                                config = {}
                            try:
                                validator = validators[ext] = class_(**config)
                            except TypeError:
                                logger.error("Cannot use '%s' without config", class_.__name__)
                if not validator:
                    no_validators.add(ext)
                    logger.info("No validator found for file extension '%s'", ext)
                    continue

                try:
                    code, message = validator.validate(os.path.abspath(path), ext)
                    report.write(path, str(code), message)
                    report.newline()
                except Exception as e:
                    logger.exception("Validating '%s' failed", path)

if __name__ == "__main__":
    import argparse

    # from genutility.os import get_appdata_dir
    from genutility.compat.os import makedirs

    parser = argparse.ArgumentParser(description="FileValidator", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #parser.add_argument("-d", "--reportdir", dest="reportdir", type=fromfs, default=os.path.join(get_appdata_dir(), "pyFileValidator"), help="set output directory for reports")
    parser.add_argument("-d", "--reportdir", dest="reportdir", type=fromfs, default="./reports", help="set output directory for reports")
    parser.add_argument("-x", "--xsl", dest="xslfile", type=fromfs, default="report.xsl", help="set xsl style sheet file")
    parser.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="scan directories recursively")
    parser.add_argument("-v", "--verbose", action="store_true", help="output debug info")
    parser.add_argument("-i", "--ignore", nargs='+', default=[], help="extensions to ignore")
    parser.add_argument("paths", metavar="DIRECTORY", nargs='+', type=fromfs, help="directories to create report for")
    args = parser.parse_args()

    if not os.path.isdir(args.reportdir):
        try:
            makedirs(args.reportdir)
        except OSError:
            exit("Error: '{}' is not a valid directory.".format(args.reportdir))

    main(args.paths, args.reportdir, args.xslfile, args.recursive, args.verbose, set(args.ignore))
