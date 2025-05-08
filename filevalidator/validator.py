import logging
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from importlib import import_module
from os import fspath
from pathlib import Path
from typing import Dict, Optional, Sequence

from genutility.args import is_dir, is_file, out_dir, suffix_lower_raw
from genutility.datetime import now
from genutility.filesystem import MyDirEntry, entrysuffix, filter_recall, scandir_error_log_warning, scandir_rec
from genutility.json import read_json
from genutility.rich import Progress
from platformdirs import user_config_dir
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.progress import BarColumn, MofNCompleteColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as RichProgress

from . import plugins
from .plug import Filetypes, Plugin, PluginError
from .report import JsonReport, ReportBase, Stdout, XmlReport, load_report

logger = logging.getLogger(__name__)

DEFAULT_REPORTS_DIR = Path("./reports")
DEFAULT_STYLE_SHEET = "report.xsl"
APP_NAME = "file-validator"
APP_AUTHOR = "Dobatymo"

USER_CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))


def scan(paths: Sequence[Path], recursive: bool, relative: bool, recall: bool):
    for path in paths:
        yield from filter(
            filter_recall(recall),
            scandir_rec(
                path,
                dirs=False,
                rec=recursive,
                follow_symlinks=False,
                relative=relative,
                errorfunc=scandir_error_log_warning,
            ),
        )


def validate_paths(
    paths: Sequence[Path],
    output: ReportBase,
    resumefile: Optional[Path] = None,
    recursive: bool = False,
    relative: bool = False,
    recall: bool = False,
    only: Optional[set] = None,
    ignore: Optional[set] = None,
) -> None:
    for name in plugins.__all__:
        try:
            import_module(".plugins." + name, __package__)
        except ModuleNotFoundError as e:
            logger.error("Skipped plugin %s due to missing dependencies: %s", name, e)

    for class_, extensions in Filetypes.PLUGINS.items():
        logger.info("Loaded Filetype plugin %s for: %s", class_.__name__, ", ".join(extensions))

    if resumefile:
        resume_info = load_report(resumefile)
    else:
        resume_info = {}

    validators: Dict[str, Plugin] = {}
    no_validators = ignore or set()

    columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ]

    with output as report, RichProgress(*columns) as progress:
        p = Progress(progress)
        for entry in p.track(scan(paths, recursive, relative, recall)):
            logger.debug("Processing `%s`", fspath(entry))
            ext = entrysuffix(entry).lower()[1:]

            if relative:
                assert isinstance(entry, MyDirEntry)
                outpath = entry.relpath
            else:
                outpath = fspath(entry)

            if ext in no_validators:
                continue

            if only and ext not in only:
                no_validators.add(ext)
                continue

            # check if resume info available

            try:
                code, message = resume_info[outpath]
            except KeyError:
                pass
            else:
                logger.debug("Copied information for %s", outpath)
                report.write(outpath, code, message)
                continue

            # get validator for ext

            validator = None
            try:
                validator = validators[ext]
            except KeyError:
                for class_, extensions in Filetypes.PLUGINS.items():
                    if ext in extensions:
                        try:
                            config = read_json(USER_CONFIG_DIR / "config" / "{class_.__name__}.json")
                        except FileNotFoundError:
                            logger.info("Could not find config for plugin '%s'", class_.__name__)
                            config = {}
                        except ValueError:
                            logger.exception("Could not load config for plugin '%s'", class_.__name__)
                            config = {}
                        try:
                            validator = validators[ext] = class_(**config)
                        except TypeError:
                            logger.error("Cannot use plugin '%s' without config", class_.__name__)
                        except PluginError as e:
                            logger.error("Cannot load plugin '%s': %s", class_.__name__, e)

            if not validator:
                no_validators.add(ext)
                logger.info("No validator found for file extension '%s'", ext)
                continue

            # validate file

            try:
                code, message = validator.validate(fspath(entry), ext)
            except KeyboardInterrupt:
                logger.warning("Validating '%s' interrupted", fspath(entry))
                raise
            except PluginError as e:
                logger.warning("Validating '%s' failed: %s", fspath(entry), e)
            except Exception:
                logger.exception("Validating '%s' failed", fspath(entry))
            else:
                report.write(outpath, code, message)


# from gooey import Gooey
# @Gooey
def main():
    parser = ArgumentParser(description="FileValidator", formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-d",
        "--reportdir",
        type=out_dir,
        default=DEFAULT_REPORTS_DIR,
        help="set output directory for reports",
    )
    parser.add_argument(
        "-x",
        "--xsl",
        dest="xslfile",
        default=DEFAULT_STYLE_SHEET,
        help="set XSL style sheet file",
    )
    parser.add_argument("-r", "--recursive", action="store_true", help="scan directories recursively")
    parser.add_argument("-v", "--verbose", action="store_true", help="output debug info")
    parser.add_argument(
        "--only",
        metavar="EXT",
        nargs="+",
        type=suffix_lower_raw,
        default=None,
        help="only include these extensions",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        metavar="EXT",
        nargs="+",
        type=suffix_lower_raw,
        default=None,
        help="extensions to ignore",
    )
    parser.add_argument("--relative", action="store_true", help="Output relative paths")
    parser.add_argument(
        "--recall",
        action="store_true",
        help="Download files which are currently only available online (on OneDrive for example), otherwise they are skipped.",
    )
    parser.add_argument("--resume", type=is_file, help="Resume validation using a previous XML report")
    parser.add_argument(
        "paths",
        metavar="DIRECTORY",
        nargs="+",
        type=is_dir,
        help="directories to create report for",
    )
    parser.add_argument(
        "--out",
        choices=("xml", "json", "stdout"),
        default="xml",
        help="Output method. xml: write to xml file, json: write to json file, stdout: simple format written to stdout",
    )
    args = parser.parse_args()

    handler = RichHandler(log_time_format="%Y-%m-%d %H-%M-%S%Z", highlighter=NullHighlighter())
    FORMAT = "%(message)s"

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=FORMAT, handlers=[handler])
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT, handlers=[handler])

    only = set(args.only) if args.only else None
    ignore = set(args.ignore) if args.ignore else None

    if args.out == "xml":
        filename = "report_{}.xml".format(now().isoformat("_").replace(":", "."))
        reportpath = args.reportdir / filename
        output = XmlReport(reportpath, args.xslfile)
        logger.info("Writing report to `%s`", reportpath)
    elif args.out == "json":
        filename = "report_{}.json".format(now().isoformat("_").replace(":", "."))
        reportpath = args.reportdir / filename
        output = JsonReport(reportpath)
        logger.info("Writing report to `%s`", reportpath)
    elif args.out == "stdout":
        output = Stdout()
    else:
        parser.error("Invalid --out method")

    logger.info("Reading configs from %s", USER_CONFIG_DIR / "config")

    validate_paths(
        args.paths,
        output,
        args.resume,
        args.recursive,
        args.relative,
        args.recall,
        only,
        ignore,
    )


if __name__ == "__main__":
    main()
