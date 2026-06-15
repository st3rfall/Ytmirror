import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "yt_downloader.py"


def load_module():
    spec = importlib.util.spec_from_file_location("yt_downloader", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_yt_dlp_args_uses_proxy_and_output_template():
    module = load_module()

    args = module.build_yt_dlp_args(
        url="https://youtu.be/example",
        output_dir="downloads",
        proxy="http://proxy.local:8080",
    )

    # URL gets normalized from youtu.be to youtube.com format
    assert "https://www.youtube.com/watch?v=example" in args
    assert "--proxy" in args
    assert "http://proxy.local:8080" in args
    assert "downloads/%(title)s.%(ext)s" in args


def test_detect_proxy_falls_back_to_all_proxy(monkeypatch):
    module = load_module()

    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("ALL_PROXY", raising=False)
    monkeypatch.setenv("all_proxy", "socks5h://school-proxy:1080")

    assert module.detect_proxy() == "socks5h://school-proxy:1080"


def test_normalize_url_converts_invidious_to_youtube():
    module = load_module()

    # Test Invidious URL
    invidious_url = "https://invidious.io/watch?v=dQw4w9WgXcQ&t=10s"
    result = module.normalize_url(invidious_url)
    assert result == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Test youtu.be shortlink
    shortlink = "https://youtu.be/dQw4w9WgXcQ"
    result = module.normalize_url(shortlink)
    assert result == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Test YouTube URL (should remain unchanged)
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = module.normalize_url(youtube_url)
    assert result == youtube_url


def test_build_yt_dlp_args_handles_invidious_urls():
    module = load_module()

    # Test with Invidious URL
    args = module.build_yt_dlp_args(
        url="https://invidious.io/watch?v=dQw4w9WgXcQ",
        output_dir="downloads",
        proxy=None,
    )

    # Should convert to YouTube URL
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in args
    assert "downloads/%(title)s.%(ext)s" in args
    assert "--proxy" not in args


def test_list_invidious_instances():
    module = load_module()
    
    # Check that instances are defined
    assert len(module.INVIDIOUS_INSTANCES) > 0
    assert all(isinstance(instance, str) for instance in module.INVIDIOUS_INSTANCES)
    assert any("invidious" in instance.lower() or "yewtu" in instance.lower() 
               for instance in module.INVIDIOUS_INSTANCES)
