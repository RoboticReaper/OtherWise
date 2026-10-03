#!/usr/bin/env python3
"""Stop only the demo processes recorded for this repository."""

import sys
import argparse

from demo_runtime import ROOT, DemoError, read_connection, runtime_lock, stop_record


def stop():
    with runtime_lock(ROOT):
        record = read_connection(ROOT)
        if record is None:
            print("No recorded OtherWise demo is running.")
            return
        count = stop_record(record, ROOT)
        (ROOT / ".cache/demo/connection.json").unlink(missing_ok=True)
        print(f"OtherWise demo stopped ({count} owned processes). The saved token was removed.")
        print("Unrelated or reused process IDs were left untouched.")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        stop()
    except DemoError as exception:
        print(f"Could not stop OtherWise: {exception}", file=sys.stderr)
        return 1
    except Exception:
        print("Could not safely stop OtherWise. Existing process metadata was preserved.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
