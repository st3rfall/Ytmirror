#!/usr/bin/env python3
"""School-friendly Ytmirror launcher.

This wrapper forces `yt_downloader.py` into school-friendly mode, which tries
Invidious direct downloads first and respects proxy environment variables.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yt_downloader


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(
            "Usage: python school.py <URL> [--output-dir DIR] [--proxy URL] "
            "[--invidious-instance INSTANCE]"
        )
        return 1

    return yt_downloader.main(["--school-mode"] + argv)


if __name__ == "__main__":
    raise SystemExit(main())
