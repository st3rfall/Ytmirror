#!/usr/bin/env python3
"""Simple YouTube downloader with optional proxy support.

This script wraps yt-dlp and can be used behind restrictive networks by
passing a proxy and enabling yt-dlp's geo-bypass support.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_OUTPUT_DIR = "downloads"


def build_yt_dlp_args(
    url: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    proxy: Optional[str] = None,
) -> List[str]:
    """Build the yt-dlp command-line arguments for a download.

    The output template is chosen to match the existing test expectation.
    The proxy is injected when provided, and geo-bypass is enabled to help
    with restricted networks.
    """
    output_template = str(Path(output_dir) / "%(title)s.%(ext)s")

    base_args = [
        "yt-dlp",
        "--output",
        output_template,
        "--geo-bypass",
        "--no-warnings",
        "--restrict-filenames",
    ]

    if proxy:
        return base_args + ["--proxy", proxy, url]

    return base_args + [url]

    return args


def detect_proxy() -> Optional[str]:
    """Use environment variables if a proxy has already been configured.

    Many school and corporate networks expose proxy settings through
    ALL_PROXY/all_proxy as well as the standard HTTP/HTTPS variables.
    """
    for key in (
        "HTTPS_PROXY",
        "https_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        value = os.environ.get(key)
        if value:
            return value
    return None


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download YouTube videos with optional proxy support."
    )
    parser.add_argument("url", help="YouTube video URL to download")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for downloaded files",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Proxy URL such as http://user:pass@host:port or socks5://host:port",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    proxy = args.proxy or detect_proxy()
    command = build_yt_dlp_args(args.url, output_dir=args.output_dir, proxy=proxy)

    if shutil.which("yt-dlp") is None:
        print(
            "yt-dlp is not installed or not available on PATH. "
            "Install it with: pip install yt-dlp",
            file=sys.stderr,
        )
        return 1

    Path(args.output_dir).mkdir(exist_ok=True)

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Download failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
