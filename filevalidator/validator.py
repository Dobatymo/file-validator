import logging
import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from contextlib import suppress
from importlib import import_module
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
from .report import JsonReport, ReportBase, ReportData, ReportEntry, Stdout, XmlReport, load_report

logger = logging.getLogger(__name__)

DEFAULT_REPORTS_DIR = Path("./reports")
DEFAULT_STYLE_SHEET = "report.xsl"
APP_NAME = "file-validator"
APP_AUTHOR = "Dobatymo"

USER_CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
ALLOW_RESUME_BASE_CHANGE_FLAG = "--allow-resume-base-change"


def get_relative_report_base(paths: Sequence[Path], relative: bool) -> Optional[str]:
    if not relative:
        return None
    if len(paths) != 1:
        raise ValueError("--relative requires exactly one input directory")
    return os.path.abspath(paths[0])


def normalize_base(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def load_resume_info(
    resumefile: Optional[Path],
    paths: Sequence[Path],
    relative: bool,
    allow_resume_base_change: bool = False,
) -> ReportData:
    if resumefile is None:
        return ReportData()

    resume_info = load_report(resumefile)
    current_base = get_relative_report_base(paths, relative)
    if current_base is not None and resume_info.base is not None and not allow_resume_base_change:
        if normalize_base(resume_info.base) != normalize_base(current_base):
            raise ValueError(
                f"Resume report base {resume_info.base!r} does not match current --relative base {current_base!r}. "
                f"Use {ALLOW_RESUME_BASE_CHANGE_FLAG} to reuse resume data from a different base."
            )
    return resume_info


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
    recursive: bool = False,
    relative: bool = False,
    recall: bool = False,
    only: Optional[set] = None,
    ignore: Optional[set] = None,
    resume_info: Optional[ReportData] = None,
) -> None:
    get_relative_report_base(paths, relative)

    if resume_info is None:
        resume_info = ReportData()

    for name in plugins.__all__:
        try:
            import_module(".plugins." + name, __package__)
        except ModuleNotFoundError as e:
            logger.error("Skipped plugin %s due to missing dependencies: %s", name, e)

    for class_, extensions in Filetypes.PLUGINS.items():
        logger.info("Loaded Filetype plugin %s for: %s", class_.__name__, ", ".join(extensions))

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
            logger.debug("Processing `%s`", os.fspath(entry))
            ext = entrysuffix(entry).lower()[1:]

            if relative:
                assert isinstance(entry, MyDirEntry)
                outpath = entry.relpath
            else:
                outpath = os.fspath(entry)

            if ext in no_validators:
                continue

            if only and ext not in only:
                no_validators.add(ext)
                continue

            try:
                stat = os.stat(entry)
            except OSError as e:
                logger.warning("Could not stat '%s' before validation: %s", os.fspath(entry), e)
                continue

            # check if resume info available

            try:
                resume_entry = resume_info[outpath]
            except KeyError:
                pass
            else:
                if resume_entry.size == stat.st_size and (
                    resume_entry.mtime_ns is None or resume_entry.mtime_ns == stat.st_mtime_ns
                ):
                    logger.debug("Copied information for %s", outpath)
                    report.write(outpath, resume_entry)
                    continue
                logger.debug("Ignoring stale resume information for %s", outpath)

            # get validator for ext

            validator = None
            try:
                validator = validators[ext]
            except KeyError:
                for class_, extensions in Filetypes.PLUGINS.items():
                    if ext in extensions:
                        config_path = USER_CONFIG_DIR / "config" / f"{class_.__name__}.json"
                        try:
                            config = read_json(config_path)
                        except FileNotFoundError:
                            logger.info(
                                "Could not find config for plugin '%s' (%s)", class_.__name__, os.fspath(config_path)
                            )
                            config = {}
                        except ValueError:
                            logger.exception(
                                "Could not load config for plugin '%s' (%s)", class_.__name__, os.fspath(config_path)
                            )
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
                code, message = validator.validate(os.fspath(entry), ext, stat.st_size)
            except KeyboardInterrupt:
                logger.warning("Validating '%s' interrupted", os.fspath(entry))
                raise
            except OSError as e:
                logger.warning("Validating '%s' failed due to file access error: %s", os.fspath(entry), e)
                report.write(
                    outpath,
                    ReportEntry(code=-1, message=str(e), size=stat.st_size, mtime_ns=stat.st_mtime_ns),
                )
            except PluginError as e:
                logger.warning("Validating '%s' failed: %s", os.fspath(entry), e)
            except Exception:
                logger.exception("Validating '%s' failed", os.fspath(entry))
            else:
                report.write(
                    outpath,
                    ReportEntry(code=code, message=message, size=stat.st_size, mtime_ns=stat.st_mtime_ns),
                )


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
        ALLOW_RESUME_BASE_CHANGE_FLAG,
        action="store_true",
        help="Allow --resume to reuse relative report entries even when the stored report base differs from the current input directory",
    )
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

    try:
        report_base = get_relative_report_base(args.paths, args.relative)
    except ValueError as e:
        parser.error(str(e))

    try:
        resume_info = load_resume_info(args.resume, args.paths, args.relative, args.allow_resume_base_change)
    except ValueError as e:
        parser.error(str(e))

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
        output = XmlReport(reportpath, args.xslfile, base=report_base)
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

    with suppress(OSError):
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    validate_paths(
        args.paths,
        output,
        args.recursive,
        args.relative,
        args.recall,
        only,
        ignore,
        resume_info=resume_info,
    )


if __name__ == "__main__":
    main()
