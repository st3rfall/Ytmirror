#!/usr/bin/env python3
"""Simple YouTube/Invidious downloader with optional proxy support.

This script wraps yt-dlp and can be used behind restrictive networks by
passing a proxy and enabling yt-dlp's geo-bypass support.
Supports downloading from YouTube and Invidious instances.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_OUTPUT_DIR = "downloads"
INVIDIOUS_INSTANCES = [
    "https://invidious.io",
    "https://yewtu.be",
    "https://invidious.namazso.eu",
    "https://invidious.weblibre.org",
]


def normalize_url(url: str) -> str:
    """Convert Invidious URLs to YouTube URLs or return original.
    
    Converts URLs like https://invidious.io/watch?v=... to
    https://www.youtube.com/watch?v=...
    """
    # Extract video ID from various formats
    if "watch?v=" in url:
        video_id = url.split("watch?v=")[1].split("&")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def build_yt_dlp_args(
    url: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    proxy: Optional[str] = None,
) -> List[str]:
    """Build the yt-dlp command-line arguments for a download.

    The output template is chosen to match the existing test expectation.
    The proxy is injected when provided, and geo-bypass is enabled to help
    with restricted networks.
    Supports YouTube and Invidious URLs.
    """
    # Normalize Invidious URLs to YouTube
    normalized_url = normalize_url(url)
    
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
        return base_args + ["--proxy", proxy, normalized_url]

    return base_args + [normalized_url]


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
        description="Download YouTube/Invidious videos with optional proxy support."
    )
    parser.add_argument("url", nargs="?", default=None, help="YouTube or Invidious video URL to download")
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
    parser.add_argument(
        "--list-invidious",
        action="store_true",
        help="List available Invidious instances",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    if args.list_invidious:
        print("Available Invidious instances:")
        for instance in INVIDIOUS_INSTANCES:
            print(f"  {instance}")
        return 0

    if not args.url:
        print("Error: URL is required when not using --list-invidious", file=sys.stderr)
        return 1

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
