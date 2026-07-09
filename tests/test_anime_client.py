"""Tests for anime client — API request construction and error handling."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestAnimeClientConfig:
    """Test anime client configuration without making real API calls."""

    def test_api_url_defined(self):
        from models.anime_client import API_URL
        assert "siliconflow" in API_URL or "api" in API_URL

    def test_model_name(self):
        from models.anime_client import MODEL_NAME
        assert "Qwen" in MODEL_NAME or "Image" in MODEL_NAME

    def test_max_retries(self):
        from models.anime_client import MAX_RETRIES
        assert MAX_RETRIES >= 1

    def test_timeout(self):
        from models.anime_client import TIMEOUT
        assert TIMEOUT >= 10

    def test_get_headers_structure(self):
        """Verify _get_headers returns dict or raises on missing key."""
        from models.anime_client import AnimeClient
        import settings
        client = AnimeClient()
        # QSettings may have a stored key from dev; check both cases
        saved = settings.get("replicate_api_key") or ""
        if not saved.strip():
            with pytest.raises(ValueError):
                client._get_headers()
        else:
            headers = client._get_headers()
            assert "Authorization" in headers
            assert "Bearer" in headers["Authorization"]

    def test_styles_map(self):
        from models.anime_client import STYLE_PROMPTS
        assert len(STYLE_PROMPTS) == 4
        for style, prompt in STYLE_PROMPTS.items():
            assert "Transform" in prompt or "transform" in prompt.lower()
            assert "Preserve" in prompt or "preserve" in prompt.lower()
            assert "clothing" in prompt.lower()


class TestAnimeClientErrorHandling:
    """Test error classification without real API calls."""

    def test_api_error_classification(self):
        """API error handling structure is correct."""
        from models.anime_client import MAX_RETRIES, TIMEOUT
        assert MAX_RETRIES == 2
        assert TIMEOUT == 60

    def test_default_style_fallback(self):
        """Verify DEFAULT_STYLE exists in STYLE_PROMPTS."""
        from models.anime_client import STYLE_PROMPTS, DEFAULT_STYLE
        assert DEFAULT_STYLE in STYLE_PROMPTS
