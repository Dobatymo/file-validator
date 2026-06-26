import logging
import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from genutility.args import is_dir, is_file
from send2trash import send2trash

from .report import ReportEntry, load_report


class FileMetadataMismatch(ValueError):
    pass


def resolve_report_path(path: str, report_base: Optional[str] = None, override_base: Optional[Path] = None) -> str:
    if os.path.isabs(path):
        return path

    if override_base is not None:
        base = os.path.abspath(override_base)
    elif report_base is None:
        raise ValueError("Report contains relative paths but does not specify a base directory; use --base")
    elif not os.path.isabs(report_base):
        raise ValueError("Report contains a relative base directory; use --base to provide an absolute directory")
    else:
        base = report_base

    return os.path.abspath(os.path.join(base, path))


def validate_file_metadata(path: str, entry: ReportEntry, ignore_mtime: bool = False) -> None:
    stat = os.stat(path)
    if stat.st_size != entry.size:
        raise FileMetadataMismatch(f"File size changed from {entry.size} to {stat.st_size}")
    if not ignore_mtime and entry.mtime_ns is not None and stat.st_mtime_ns != entry.mtime_ns:
        raise FileMetadataMismatch(f"File modification time changed from {entry.mtime_ns} to {stat.st_mtime_ns}")


def trash_invalid(path: str, entry: ReportEntry, ignore_mtime: bool = False) -> bool:
    if entry.code != 1 or not entry.message:
        return False

    validate_file_metadata(path, entry, ignore_mtime)
    send2trash(path)
    return True


def main():
    ACTIONS = {"trash-invalid": trash_invalid}

    parser = ArgumentParser()
    parser.add_argument("report", type=is_file)
    parser.add_argument("--action", choices=ACTIONS.keys(), required=True)
    parser.add_argument(
        "--message-cmp", default=None, help="Optionally compare the messages before applying the action"
    )
    parser.add_argument(
        "--message-in", default=None, help="Optionally check for this string in message before applying the action"
    )
    parser.add_argument(
        "--ignore-mtime",
        action="store_true",
        help="Ignore modification-time changes, but still require the file size to match the report",
    )
    parser.add_argument(
        "--base",
        type=is_dir,
        help="Override the base directory stored in the report for relative paths",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        report = load_report(args.report)
    except ValueError as e:
        parser.error(str(e))

    try:
        paths = {
            path: resolve_report_path(path, report_base=report.base, override_base=args.base) for path in report.keys()
        }
    except ValueError as e:
        parser.error(str(e))

    func = ACTIONS[args.action]

    processed = 0
    skipped = 0
    file_not_found = 0
    failed = 0

    for report_path, entry in report.items():
        path = paths[report_path]
        if args.message_cmp and args.message_cmp != entry.message:
            logging.info("Skipping (%s): %s (%d) [%s]", func.__name__, path, entry.code, entry.message[:100])
            skipped += 1
            continue

        if args.message_in and args.message_in not in entry.message:
            logging.info("Skipping (%s): %s (%d) [%s]", func.__name__, path, entry.code, entry.message[:100])
            skipped += 1
            continue

        logging.debug("Processing (%s): %s (%d) [%s]", func.__name__, path, entry.code, entry.message[:100])
        try:
            if func(path, entry, args.ignore_mtime):
                processed += 1
                logging.info("Processed (%s): %s", func.__name__, path)
            else:
                skipped += 1
        except FileMetadataMismatch as e:
            logging.warning("Skipping changed file (%s): %s: %s", func.__name__, path, e)
            skipped += 1
        except FileNotFoundError:
            logging.debug("Processing failed (file-not-found) (%s): %s", func.__name__, path)
            file_not_found += 1
        except OSError as e:
            if e.errno == 3:
                logging.debug("Processing failed (file-not-found) (%s): %s", func.__name__, path)
                file_not_found += 1
            else:
                logging.error("Processing failed (%s): %s", func.__name__, path)
                failed += 1
                print(e.errno)
        except Exception:
            logging.error("Processing failed (%s): %s", func.__name__, path)
            failed += 1

    print("processed", processed, "skipped", skipped, "file_not_found", file_not_found, "failed", failed)


if __name__ == "__main__":
    main()
