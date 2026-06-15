#!/usr/bin/env python3
"""
Ytmirror - YouTube & Invidious Downloader
Easy launcher that opens the web interface automatically.

Usage:
    python app.py              # Opens in browser with web server
    python app.py --cli        # Use command-line interface only
"""

import argparse
import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from threading import Thread
from time import sleep

# Add the current directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))


def ensure_dependencies():
    """Ensure all required dependencies are installed."""
    required_packages = {
        "yt_dlp": "yt-dlp",
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("📦 Installing required dependencies (if possible)...")
        for package in missing_packages:
            print(f"   Installing {package} via pip...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-q", package]
                )
                print(f"   ✓ {package} installed")
            except subprocess.CalledProcessError:
                print(f"   ✗ Failed to install {package} via pip")
                print("   Will attempt to download standalone yt-dlp binary instead")
                # Attempt to download standalone binary for yt-dlp
                if package == "yt-dlp":
                    try:
                        download_dir = Path(__file__).parent / "bin"
                        download_dir.mkdir(exist_ok=True)
                        binary_path = download_dir / "yt-dlp"
                        if not binary_path.exists():
                            import urllib.request

                            url = (
                                "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
                            )
                            print(f"   Downloading yt-dlp binary from {url}...")
                            urllib.request.urlretrieve(url, str(binary_path))
                            binary_path.chmod(0o755)
                            print(f"   ✓ yt-dlp binary downloaded to {binary_path}")
                        else:
                            print(f"   ✓ yt-dlp binary already present at {binary_path}")
                    except Exception as e:
                        print(f"   ✗ Failed to download yt-dlp binary: {e}")
                        print(f"   Please install manually: pip install {package}")
                        sys.exit(1)
        print("✓ Dependency step completed\n")


# Ensure dependencies before importing modules
ensure_dependencies()

import web_server
import yt_downloader


def main():
    parser = argparse.ArgumentParser(
        description="Ytmirror - Download from YouTube & Invidious",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                      # Open web interface (recommended)
  python app.py --port 9000          # Use custom port
  python app.py --cli URL            # Download via CLI
  python app.py --list-invidious     # List Invidious instances
        """
    )
    
    parser.add_argument(
        "--cli",
        nargs="?",
        const=True,
        metavar="URL",
        help="Use command-line mode (optionally with a URL)"
    )
    parser.add_argument(
        "--list-invidious",
        action="store_true",
        help="List available Invidious instances"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for web server (default: localhost)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start server without opening browser"
    )
    
    # Parse known args to handle CLI mode
    args, remaining = parser.parse_known_args()
    
    # Handle list-invidious
    if args.list_invidious:
        return yt_downloader.main(["--list-invidious"])
    
    # Handle CLI mode
    if args.cli:
        if args.cli is True and remaining:
            # URL was passed as positional arg
            return yt_downloader.main([remaining[0]] + remaining[1:])
        elif args.cli is True:
            print("Error: URL required in CLI mode", file=sys.stderr)
            return 1
        else:
            # args.cli is the URL
            return yt_downloader.main([args.cli] + remaining)
    
    # Web mode (default)
    return start_web_interface(args.host, args.port, args.no_browser)


def start_web_interface(host: str, port: int, no_browser: bool = False) -> int:
    """Start the web server and open in browser."""
    url = f"http://{host}:{port}"
    
    # Start server in a thread
    def run_server():
        try:
            web_server.main([f"--host", host, f"--port", str(port)])
        except KeyboardInterrupt:
            pass
    
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    sleep(1)
    
    # Open browser unless --no-browser flag
    if not no_browser:
        try:
            webbrowser.open(url)
            print(f"✓ Opening {url} in your browser...")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open {url} manually")
    else:
        print(f"✓ Server running at {url}")
    
    print("Press Ctrl+C to stop")
    
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        return 0
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
