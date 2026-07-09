"""Fashion reference search — SerpAPI integration."""
import logging
from urllib.parse import urlencode

import requests

from settings import get as get_setting

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"
TIMEOUT = 10


class SearchClient:
    """Searches for fashion references and suggestions."""

    def search(self, items: list[dict], style_tags: list[str]) -> dict:
        """
        Search for fashion references based on outfit items.

        Returns:
            {"suggestions": [...], "references": [{"title": "", "url": ""}]}
        """
        api_key = (get_setting("search_api_key") or "").strip()
        if not api_key:
            logger.warning("No search API key configured")
            return self._fallback(items, style_tags)

        query = self._build_query(items, style_tags)
        logger.info(f"Search query: {query}")

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": 5,
                "hl": "zh-CN",
                "gl": "cn",
            }
            resp = requests.get(SERPAPI_URL, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                logger.error(f"Search API error: {data['error']}")
                return self._fallback(items, style_tags)

            results = data.get("organic_results", [])
            refs = []
            raw_suggestions = []

            for r in results[:5]:
                title = r.get("title", "")
                url = r.get("link", "")
                snippet = r.get("snippet", "")
                if url:
                    refs.append({"title": title, "url": url})
                if snippet:
                    raw_suggestions.append(snippet)

            suggestions = self._extract_suggestions(raw_suggestions, items)
            return {"suggestions": suggestions, "references": refs}

        except requests.Timeout:
            logger.warning("Search API timeout")
            return self._fallback(items, style_tags)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._fallback(items, style_tags)

    def _build_query(self, items: list[dict], style_tags: list[str]) -> str:
        parts = []
        for item in items[:3]:
            name = item.get("name", "")
            color = item.get("color", "")
            cat = item.get("category", "")
            if name and name != "—":
                part = f"{color} {name}" if color and color != "—" else name
                parts.append(part)

        query = " ".join(parts) if parts else "日常穿搭"
        if style_tags:
            query += f" {style_tags[0]}风格"
        query += " 搭配建议 时尚"
        return query

    def _extract_suggestions(self, snippets: list[str], items: list[dict]) -> list[str]:
        """Extract actionable suggestions from search snippets."""
        suggestions = []

        # Also generate local rule-based suggestions
        local = self._local_suggestions(items)
        suggestions.extend(local)

        # Add snippets as-is (trimmed)
        for s in snippets[:3]:
            short = s.strip()
            if len(short) > 100:
                short = short[:97] + "..."
            if short and short not in suggestions:
                suggestions.append(short)

        return suggestions[:5]

    def _local_suggestions(self, items: list[dict]) -> list[str]:
        """Generate rule-based suggestions from items."""
        tips = []
        colors = [it.get("color", "") for it in items if it.get("color") != "—"]
        categories = [it.get("category", "") for it in items]
        n = len(items)

        if n <= 1:
            tips.append("尝试增加配饰提升整体层次感")
        if "配饰" not in categories:
            tips.append("搭配一件饰品（手表、项链或帽子）让造型更有亮点")
        if "外套" not in categories:
            tips.append("外搭一件夹克或开衫，适应温差变化的同时增加造型层次")
        if len(set(colors)) <= 2 and len(colors) >= 2:
            tips.append("考虑加入一个对比色单品打破单调")
        if "鞋子" not in categories:
            tips.append("选一双合适的鞋子完成整体造型")
        return tips[:4]

    def _fallback(self, items: list[dict], style_tags: list[str]) -> dict:
        """Return local suggestions only when search is unavailable."""
        suggestions = self._local_suggestions(items)
        return {"suggestions": suggestions, "references": []}
