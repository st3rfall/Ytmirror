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

    assert "https://youtu.be/example" in args
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
