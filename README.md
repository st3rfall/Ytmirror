# Ytmirror

A simple, feature-rich downloader for YouTube and Invidious videos with optional proxy support.

## Features

✨ **Easy to use** - Simple CLI and web interface  
🎯 **YouTube & Invidious** - Download from both YouTube and Invidious instances  
🌐 **Proxy support** - Works behind restrictive networks  
📥 **Standalone HTML** - Download the HTML file and use it directly  
⚙️ **Flexible** - Configure output directory, proxy settings, and more  

## Quick Start

### 1. Install Dependencies

```bash
pip install yt-dlp
```

### 2. Easiest Way - Launch with One Command

```bash
python app.py
```

This will automatically open the web interface in your browser and start the server.

### 3. Alternative Methods

#### Web Interface with Web Server

```bash
python web_server.py
```

Then open http://localhost:8000 in your browser.

#### Use Standalone HTML

Download `index.html` and open it in your browser. If you don't have the web server running, you can still use the CLI instructions provided in the interface.

### 4. Command Line

Download a YouTube video:

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Download from Invidious:

```bash
python yt_downloader.py "https://invidious.io/watch?v=dQw4w9WgXcQ"
```

### Advanced CLI Options

#### With Proxy

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=..." --proxy "http://proxy:8080"
```

Or use environment variables:

```bash
export HTTP_PROXY=http://proxy:8080
python yt_downloader.py "https://www.youtube.com/watch?v=..."
```

#### Custom Output Directory

```bash
python yt_downloader.py "https://www.youtube.com/watch?v=..." --output-dir "my_videos"
```

#### List Available Invidious Instances

```bash
python yt_downloader.py --list-invidious
```

## Launcher Script

Use the `app.py` launcher for the easiest experience:

```bash
# Open web interface in browser (recommended)
python app.py

# Use custom port
python app.py --port 9000

# Command-line mode
python app.py --cli "https://www.youtube.com/watch?v=xxx"

# List Invidious instances
python app.py --list-invidious

# Start server without opening browser
python app.py --no-browser
```

## Invidious Instances

Invidious is an alternative YouTube frontend that respects privacy. You can use any of these instances:

- https://invidious.io
- https://yewtu.be
- https://invidious.namazso.eu
- https://invidious.weblibre.org

Just replace the instance in your URL. For example:
- YouTube: `https://www.youtube.com/watch?v=xxx`
- Invidious: `https://invidious.io/watch?v=xxx`

The tool automatically converts Invidious URLs to YouTube URLs for downloading.

## Web Server Options

### Start Server on Custom Host/Port

```bash
python web_server.py --host 0.0.0.0 --port 8080
```

### Use with Docker

```bash
docker run -it -p 8000:8000 -v $(pwd)/downloads:/app/downloads python:3.11 \
  bash -c "pip install yt-dlp && python web_server.py --host 0.0.0.0"
```

## Configuration

### Environment Variables

The tool respects standard proxy environment variables:

```bash
export HTTPS_PROXY=http://proxy:8080
export HTTP_PROXY=http://proxy:8080
export ALL_PROXY=http://proxy:8080
```

On Unix/Linux, you can also use:

```bash
export https_proxy=http://proxy:8080
export http_proxy=http://proxy:8080
export all_proxy=http://proxy:8080
```

## URL Formats Supported

| Format | Example | Source |
|--------|---------|--------|
| YouTube Standard | `https://www.youtube.com/watch?v=xxx` | youtube.com |
| YouTube Short | `https://youtu.be/xxx` | youtu.be |
| Invidious | `https://invidious.io/watch?v=xxx` | Invidious instance |

## Testing

Run the test suite:

```bash
pip install pytest
pytest tests/
```

## Releases

Each release includes an `index.html` file that you can download and use immediately:

1. Download `index.html` from the latest release
2. Open it in any web browser
3. Follow the instructions in the interface

You can also copy this file to any web server (Apache, Nginx, etc.) for shared access.

## Troubleshooting

### yt-dlp not found

Install it with:
```bash
pip install yt-dlp
```

### Download fails with "Geo-blocked" error

Try using a proxy or switching to an Invidious instance:

```bash
# With proxy
python yt_downloader.py "URL" --proxy "http://proxy:8080"

# With Invidious
python yt_downloader.py "https://invidious.io/watch?v=xxx"
```

### Issues with restricted networks

- Use `--proxy` flag to specify a proxy
- Environment variables are automatically detected
- Invidious instances may work better in some regions

## License

MIT