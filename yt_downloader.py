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
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs


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

    def get_yt_dlp_cmd() -> List[str]:
        """Return the command to invoke yt-dlp.

        Prefer the Python module if installed, otherwise use a bundled
        `bin/yt-dlp` executable in the project, or fallback to `yt-dlp`
        on PATH.
        """
        try:
            import yt_dlp  # type: ignore
            return [sys.executable, "-m", "yt_dlp"]
        except Exception:
            # Check for bundled binary in project `bin/yt-dlp` or `bin/yt-dlp.exe`
            bundled_dir = Path(__file__).parent / "bin"
            is_windows = sys.platform.startswith("win")
            bin_name = "yt-dlp.exe" if is_windows else "yt-dlp"
            bundled = bundled_dir / bin_name
            if bundled.exists():
                return [str(bundled)]
            # Try the alternate name as a fallback
            alt = bundled_dir / ("yt-dlp.exe" if not is_windows else "yt-dlp")
            if alt.exists():
                return [str(alt)]
            return ["yt-dlp"]

    base_args = get_yt_dlp_cmd() + [
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


def _extract_video_id(url: str) -> Optional[str]:
    """Extract a YouTube-style video id from YouTube or Invidious URLs."""
    parsed = urlparse(url)
    # youtu.be shortlink
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    # watch?v= on any host
    qs = parse_qs(parsed.query)
    if "v" in qs and qs["v"]:
        return qs["v"][0]
    # path might be /watch/<id> on some invidious instances
    parts = parsed.path.strip("/").split("/")
    if parts and len(parts[0]) >= 6:
        # crude fallback
        return parts[-1]
    return None


def _fetch_invidious_json(instance: str, video_id: str, timeout: int = 10) -> Optional[dict]:
    """Fetch `/api/v1/videos/{id}` JSON from an Invidious instance."""
    api_url = instance.rstrip("/") + f"/api/v1/videos/{video_id}"
    try:
        with urllib.request.urlopen(api_url, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
            return json.loads(data)
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None


def _choose_format(formats: list) -> Optional[dict]:
    """Choose the best downloadable format from Invidious `formats` list.

    Prefers progressive (non-dash) formats with highest resolution.
    """
    best = None
    for f in formats:
        # Skip dash/mpd/fragmented formats if a progressive exists
        url = f.get("url") or f.get("audio_url")
        if not url:
            continue
        # prefer non-dash
        is_progressive = not f.get("dash", False) and not f.get("is_dash", False)
        height = f.get("height") or 0
        score = (1 if is_progressive else 0, height)
        if best is None:
            best = (score, f)
            continue
        if score > best[0]:
            best = (score, f)
    return best[1] if best else None


def download_via_invidious(url: str, output_dir: str = DEFAULT_OUTPUT_DIR, proxy: Optional[str] = None) -> int:
    """Attempt to download a video using Invidious instances directly.

    Returns 0 on success, non-zero on failure.
    """
    video_id = _extract_video_id(url)
    if not video_id:
        print("Could not determine video id for Invidious fallback", file=sys.stderr)
        return 2

    for instance in INVIDIOUS_INSTANCES:
        info = _fetch_invidious_json(instance, video_id)
        if not info:
            continue
        formats = info.get("formats") or info.get("adaptive_formats") or []
        fmt = _choose_format(formats)
        if not fmt:
            continue
        media_url = fmt.get("url") or fmt.get("audio_url")
        if not media_url:
            continue

        title = info.get("title") or video_id
        ext = fmt.get("ext") or "mp4"
        out_path = Path(output_dir) / f"{title}.{ext}"
        Path(output_dir).mkdir(exist_ok=True)

        try:
            req = urllib.request.Request(media_url, headers={"User-Agent": "ytmirror/1.0"})
            with urllib.request.urlopen(req) as resp, open(out_path, "wb") as outf:
                shutil.copyfileobj(resp, outf)
            print(f"Downloaded via Invidious {instance}: {out_path}")
            return 0
        except Exception as e:
            print(f"Failed to download from {instance}: {e}")
            continue

    print("Invidious fallback failed for all instances", file=sys.stderr)
    return 3


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
    # Verify we have some way to run yt-dlp: module, bundled binary, or system
    has_module = True
    try:
        import yt_dlp  # type: ignore
    except Exception:
        has_module = False

    bundled_dir = Path(__file__).parent / "bin"
    is_windows = sys.platform.startswith("win")
    bundled = bundled_dir / ("yt-dlp.exe" if is_windows else "yt-dlp")
    # also allow alternate name
    bundled_alt = bundled_dir / ("yt-dlp" if is_windows else "yt-dlp.exe")

    # If any yt-dlp method is available, run it
    if has_module or shutil.which("yt-dlp") or bundled.exists() or bundled_alt.exists():
        Path(args.output_dir).mkdir(exist_ok=True)
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"Download failed with exit code {exc.returncode}", file=sys.stderr)
            return exc.returncode
        return 0

    # As a last resort, try Invidious-only fallback (no yt-dlp required)
    print("yt-dlp not available; attempting Invidious-only download fallback...")
    return download_via_invidious(args.url, output_dir=args.output_dir, proxy=proxy)


if __name__ == "__main__":
    raise SystemExit(main())
