"""Tests for data schema — ClothingItem / OutfitAnalysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from data.schema import ClothingItem, OutfitAnalysis


class TestClothingItem:
    def test_create_basic_item(self):
        item = ClothingItem(
            category="上衣",
            name="白色T恤",
            color="白色",
            pattern="纯色",
            confidence=0.95,
            bbox=(100, 200, 300, 400),
        )
        assert item.category == "上衣"
        assert item.name == "白色T恤"
        assert item.color == "白色"
        assert item.pattern == "纯色"
        assert item.confidence == 0.95
        assert item.bbox == (100, 200, 300, 400)

    def test_default_values(self):
        item = ClothingItem(category="鞋子", name="运动鞋", color="黑色")
        assert item.pattern == ""
        assert item.material_hint == ""
        assert item.confidence == 0.0
        assert item.bbox == (0, 0, 0, 0)

    def test_to_dict(self):
        item = ClothingItem(
            category="下装",
            name="蓝色牛仔裤",
            color="蓝色",
            pattern="纯色",
            material_hint="牛仔",
            confidence=0.88,
            bbox=(50, 400, 350, 800),
        )
        d = item.to_dict()
        assert d["category"] == "下装"
        assert d["name"] == "蓝色牛仔裤"
        assert d["color"] == "蓝色"
        assert d["pattern"] == "纯色"
        assert d["material_hint"] == "牛仔"
        assert d["confidence"] == 0.88
        assert d["bbox"] == [50, 400, 350, 800]

    def test_bbox_default(self):
        item = ClothingItem(category="配饰", name="手表", color="银色")
        assert item.bbox == (0, 0, 0, 0)


class TestOutfitAnalysis:
    def test_empty_analysis(self):
        analysis = OutfitAnalysis.empty()
        assert analysis.items == []
        assert analysis.style_tags == []
        assert analysis.score == 0
        assert analysis.season_fit == "四季"

    def test_with_items(self):
        items = [
            ClothingItem(category="上衣", name="T恤", color="黑色"),
            ClothingItem(category="下装", name="牛仔裤", color="蓝色"),
        ]
        analysis = OutfitAnalysis(
            items=items,
            style_tags=["街头休闲", "极简"],
            season_fit="春夏",
            score=7,
            score_breakdown={"配色": 7, "比例": 8, "层次": 6, "风格": 7},
            suggestions=["可以加一件外套增加层次感"],
            references=[{"title": "参考链接", "url": "https://example.com"}],
        )
        assert len(analysis.items) == 2
        assert analysis.style_tags == ["街头休闲", "极简"]
        assert analysis.season_fit == "春夏"
        assert analysis.score == 7
        assert analysis.score_breakdown["配色"] == 7

    def test_to_dict(self):
        items = [ClothingItem(category="外套", name="牛仔夹克", color="蓝色", confidence=0.9)]
        analysis = OutfitAnalysis(
            items=items,
            style_tags=["街头"],
            season_fit="秋冬",
            score=6,
            score_breakdown={"配色": 6, "比例": 6, "层次": 6, "风格": 6},
            suggestions=["建议1"],
            references=[],
        )
        d = analysis.to_dict()
        assert d["score"] == 6
        assert len(d["items"]) == 1
        assert d["items"][0]["category"] == "外套"
        assert d["tags"] == ["街头"]
        assert d["season"] == "秋冬"

    def test_empty_to_dict(self):
        analysis = OutfitAnalysis.empty()
        d = analysis.to_dict()
        assert d["items"] == []
        assert d["score"] == 0
