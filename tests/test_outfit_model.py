"""Tests for outfit model — scoring engine and model initialization."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from data.schema import ClothingItem, OutfitAnalysis


# We test the scoring logic in isolation (no model download needed)
# The actual model tests require YOLO/CLIP downloads (~600MB)

class TestScoringEngine:
    """Test the rule-based scoring engine (_compute_score logic)."""

    def _compute_score(self, items, style_tags):
        """Replica of OutfitModel._compute_score for testing."""
        n = len(items)
        breakdown = {"配色": 5, "比例": 5, "层次": 5, "风格": 5}

        colors = [it.color for it in items if it.color and it.color != "—"]
        if len(set(colors)) >= 3:
            breakdown["配色"] = 7
        elif len(set(colors)) >= 2:
            breakdown["配色"] = 6

        categories = [it.category for it in items]
        if "上衣" in categories and ("下装" in categories or "连衣裙" in categories):
            breakdown["比例"] = 7
        if "外套" in categories:
            breakdown["比例"] += 1

        if n >= 4:
            breakdown["层次"] = 8
        elif n >= 3:
            breakdown["层次"] = 7
        elif n >= 2:
            breakdown["层次"] = 5

        if len(style_tags) >= 2:
            breakdown["风格"] = 7
        elif len(style_tags) == 1:
            breakdown["风格"] = 6

        total = sum(breakdown.values())
        score = min(10, max(1, round(total / 4)))
        return score, breakdown

    def test_minimal_outfit(self):
        """2 items, 2 colors, 1 style tag."""
        items = [
            ClothingItem(category="上衣", name="T恤", color="黑色"),
            ClothingItem(category="下装", name="牛仔裤", color="蓝色"),
        ]
        score, breakdown = self._compute_score(items, ["街头"])
        assert 4 <= score <= 8
        assert breakdown["比例"] == 7  # top + bottom
        assert breakdown["层次"] == 5  # exactly 2 items

    def test_full_outfit_high_score(self):
        """4 items, multiple colors, 2 style tags."""
        items = [
            ClothingItem(category="上衣", name="衬衫", color="白色"),
            ClothingItem(category="下装", name="西裤", color="黑色"),
            ClothingItem(category="外套", name="西装", color="藏青色"),
            ClothingItem(category="鞋子", name="皮鞋", color="黑色"),
        ]
        score, breakdown = self._compute_score(items, ["正装", "极简"])
        assert score >= 7
        assert breakdown["层次"] == 8  # >= 4 items
        assert breakdown["配色"] >= 6  # >= 3 colors (or 2: white/black/navy)
        assert breakdown["比例"] >= 7  # top + bottom + bonus for jacket
        assert breakdown["风格"] == 7  # 2 style tags

    def test_single_item_low_score(self):
        """Only 1 item — lowest score."""
        items = [
            ClothingItem(category="连衣裙", name="碎花连衣裙", color="红色"),
        ]
        score, breakdown = self._compute_score(items, ["波西米亚"])
        assert score <= 6
        assert breakdown["层次"] == 5  # default, not >= 2

    def test_empty_items(self):
        """No items detected."""
        score, breakdown = self._compute_score([], [])
        assert breakdown["配色"] == 5  # defaults
        assert breakdown["层次"] == 5
        assert 1 <= score <= 5

    def test_score_bounds(self):
        """Score must always be between 1 and 10."""
        for n in range(0, 10):
            items = [ClothingItem(category="上衣", name="X", color=f"颜色{i}") for i in range(n)]
            score, _ = self._compute_score(items, ["测试"])
            assert 1 <= score <= 10, f"Score {score} out of bounds for {n} items"


class TestStylePrompts:
    """Verify CLIP prompt definitions are well-formed."""

    def test_category_prompts(self):
        from models.outfit_model import CATEGORY_PROMPTS
        assert len(CATEGORY_PROMPTS) == 6
        categories = [p[0] for p in CATEGORY_PROMPTS]
        assert "上衣" in categories
        assert "下装" in categories
        assert "连衣裙" in categories
        # Each prompt is a tuple of (label, description)
        for label, desc in CATEGORY_PROMPTS:
            assert isinstance(label, str) and len(label) > 0
            assert isinstance(desc, str) and len(desc) > 0

    def test_color_prompts(self):
        from models.outfit_model import COLOR_PROMPTS
        assert len(COLOR_PROMPTS) >= 15
        assert "黑色" in COLOR_PROMPTS
        assert "白色" in COLOR_PROMPTS

    def test_style_prompts(self):
        from models.outfit_model import STYLE_PROMPTS
        assert len(STYLE_PROMPTS) >= 10
        assert any("街头" in s for s in STYLE_PROMPTS)

    def test_season_prompts(self):
        from models.outfit_model import SEASON_PROMPTS
        assert len(SEASON_PROMPTS) == 3


class TestAnimeStylePrompts:
    """Verify anime style mappings are valid."""

    def test_styles_defined(self):
        from models.anime_client import STYLE_PROMPTS, DEFAULT_STYLE
        assert len(STYLE_PROMPTS) == 4
        assert "赛璐珞风" in STYLE_PROMPTS
        assert "新海诚风" in STYLE_PROMPTS
        assert "吉卜力风" in STYLE_PROMPTS
        assert "漫画线稿" in STYLE_PROMPTS
        assert DEFAULT_STYLE == "赛璐珞风"

    def test_prompts_non_empty(self):
        from models.anime_client import STYLE_PROMPTS
        for style, prompt in STYLE_PROMPTS.items():
            assert len(prompt) > 50, f"Prompt for {style} too short"


class TestRegionRatios:
    """Verify clothing region estimation heuristics."""

    def test_regions_defined(self):
        from models.outfit_model import REGION_RATIOS
        assert "上衣" in REGION_RATIOS
        assert "下装" in REGION_RATIOS
        assert "鞋子" in REGION_RATIOS

    def test_ratios_in_range(self):
        from models.outfit_model import REGION_RATIOS
        for category, (start, end) in REGION_RATIOS.items():
            assert 0.0 <= start <= 1.0, f"{category} start ratio out of range"
            assert 0.0 <= end <= 1.2, f"{category} end ratio out of range"
            assert start < end, f"{category} start >= end"
