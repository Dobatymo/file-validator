import logging
from argparse import ArgumentParser

from genutility.args import is_file
from send2trash import send2trash

from .report import load_report


def trash_invalid(path: str, code: int, message: str) -> None:
    if code == 1 and message:
        send2trash(path)


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
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        d = load_report(args.report)
    except ValueError as e:
        parser.error(str(e))

    func = ACTIONS[args.action]

    processed = 0
    skipped = 0
    file_not_found = 0
    failed = 0

    for path, (code, message) in d.items():
        if args.message_cmp and args.message_cmp != message:
            logging.info("Skipping (%s): %s (%d) [%s]", func.__name__, path, code, message[:100])
            skipped += 1
            continue

        if args.message_in and args.message_in not in message:
            logging.info("Skipping (%s): %s (%d) [%s]", func.__name__, path, code, message[:100])
            skipped += 1
            continue

        logging.debug("Processing (%s): %s (%d) [%s]", func.__name__, path, code, message[:100])
        try:
            func(path, code, message)
            processed += 1
            logging.info("Processed (%s): %s", func.__name__, path)
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
