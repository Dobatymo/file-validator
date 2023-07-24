from argparse import ArgumentParser

from genutility.args import is_file
from send2trash import send2trash

from xmlreport import load_report


def trash_invalid(path, code, message) -> None:
    if code == 1 and message:
        send2trash(path)


ACTIONS = {"trash-invalid": trash_invalid}

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("report", type=is_file)
    parser.add_argument("--action", choices=ACTIONS.keys())
    parser.add_argument(
        "--message-cmp", default=None, help="Optionally compare the messages before applying the action"
    )
    parser.add_argument(
        "--message-in", default=None, help="Optionally check for this string in message before applying the action"
    )
    args = parser.parse_args()

    d = load_report(args.report)
    func = ACTIONS[args.action]

    processed = 0
    skipped = 0
    failed = 0

    for path, (code, message) in d.items():
        if args.message_cmp and args.message_cmp != message:
            print("Skipping", func.__name__, path, code, message[:100])
            skipped += 1
            continue

        if args.message_in and args.message_in not in message:
            print("Skipping", func.__name__, path, code, message[:100])
            skipped += 1
            continue

        print("Processing", func.__name__, path, code, message[:100])
        try:
            func(path, code, message)
            processed += 1
        except Exception:
            print("Processing failed", func.__name__, path)
            failed += 1

    print("processed", processed, "skipped", skipped, "failed", failed)
