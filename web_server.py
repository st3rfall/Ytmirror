#!/usr/bin/env python3
"""Simple HTTP server for the Ytmirror web interface.

Serves the HTML UI and handles download requests via REST API.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse

import yt_downloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).resolve().parent
HTML_FILE = SCRIPT_DIR / "index.html"

if not HTML_FILE.exists():
    # Fallback to current working directory if running in an unusual environment
    fallback = Path.cwd() / "index.html"
    if fallback.exists():
        HTML_FILE = fallback
    else:
        logger.warning("Expected HTML file not found at %s", HTML_FILE)
        logger.warning("Also checked current working directory: %s", fallback)


class DownloadHandler(BaseHTTPRequestHandler):
    """HTTP request handler for downloads and static files."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/invidious-instances":
            self._serve_instances()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests for downloads."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/download":
            self._handle_download()
        else:
            self.send_error(404, "Not Found")

    def _serve_html(self):
        """Serve the HTML file."""
        if not HTML_FILE.exists():
            self.send_error(404, "HTML file not found")
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        with open(HTML_FILE, "rb") as f:
            self.wfile.write(f.read())

    def _serve_instances(self):
        """Serve list of Invidious instances."""
        instances = {
            "instances": yt_downloader.INVIDIOUS_INSTANCES
        }
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(instances).encode())

    def _handle_download(self):
        """Handle download requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body)
            url = data.get("url", "").strip()
            output_dir = data.get("output_dir", yt_downloader.DEFAULT_OUTPUT_DIR)
            proxy = data.get("proxy", "")
            
            if not url:
                self._send_json_response(400, {"error": "URL is required"})
                return
            
            # Use provided proxy or detect from environment
            proxy = proxy or yt_downloader.detect_proxy()
            
            # Build the command
            command = yt_downloader.build_yt_dlp_args(url, output_dir, proxy)
            
            # Check if yt-dlp is available
            if shutil.which("yt-dlp") is None:
                self._send_json_response(
                    500, 
                    {"error": "yt-dlp is not installed. Install with: pip install yt-dlp"}
                )
                return
            
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)
            
            # Run the download in a thread to avoid blocking
            def run_download():
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info(f"Download successful: {url}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Download failed: {e.stderr}")
            
            thread = Thread(target=run_download)
            thread.daemon = True
            thread.start()
            
            self._send_json_response(200, {
                "status": "downloading",
                "message": f"Download started for: {url}"
            })
            
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Error: {e}")
            self._send_json_response(500, {"error": str(e)})

    def _send_json_response(self, status_code: int, data: dict):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        logger.info(format % args)


def main(argv: Optional[list] = None) -> int:
    """Run the HTTP server."""
    parser = argparse.ArgumentParser(description="Run Ytmirror web server")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    
    args = parser.parse_args(argv)
    
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, DownloadHandler)
    
    url = f"http://{args.host}:{args.port}"
    logger.info(f"Starting Ytmirror server at {url}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        return 0
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
