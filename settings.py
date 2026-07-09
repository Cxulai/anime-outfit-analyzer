"""Application settings via QSettings (persisted to Windows registry / ini file)."""
from PyQt6.QtCore import QSettings
from pathlib import Path

APP_NAME = "AnimeOutfitAnalyzer"
APP_VERSION = "0.1.0"
BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "replicate_api_key": "",
    "search_api_key": "",
    "search_provider": "serpapi",  # "serpapi" | "bing"
    "default_anime_style": "赛璐珞风",
    "model_cache_dir": str(BASE_DIR / "models_cache"),
    "export_dir": str(BASE_DIR / "exports"),
    "export_format": "PNG",
    "export_quality": 95,
}

_settings = None


def get_settings() -> QSettings:
    global _settings
    if _settings is None:
        _settings = QSettings("AnimeOutfit", "Analyzer")
        for key, value in DEFAULTS.items():
            if not _settings.contains(key):
                _settings.setValue(key, value)
    return _settings


def get(key: str):
    s = get_settings()
    val = s.value(key, DEFAULTS.get(key))
    if isinstance(DEFAULTS.get(key), int):
        return int(val)
    return val


def set_(key: str, value):
    s = get_settings()
    s.setValue(key, value)
    s.sync()
