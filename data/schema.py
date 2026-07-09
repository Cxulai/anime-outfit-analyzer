"""Data models for outfit analysis results."""
from dataclasses import dataclass, field


@dataclass
class ClothingItem:
    category: str       # 上衣 | 下装 | 鞋子 | 配饰 | 外套 | 连衣裙
    name: str           # "宽松圆领T恤"
    color: str          # "黑色"
    pattern: str = ""   # 纯色 | 条纹 | 格子 | 碎花 | 迷彩 | ...
    material_hint: str = ""  # 棉质 | 牛仔 | 皮质 | 针织 | ...
    confidence: float = 0.0  # 0.0 - 1.0
    # Bounding box on the ORIGINAL image (x1, y1, x2, y2) — for annotation
    bbox: tuple = field(default_factory=lambda: (0, 0, 0, 0))

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "name": self.name,
            "color": self.color,
            "pattern": self.pattern,
            "material_hint": self.material_hint,
            "confidence": self.confidence,
            "bbox": list(self.bbox),
        }


@dataclass
class OutfitAnalysis:
    items: list[ClothingItem] = field(default_factory=list)
    style_tags: list[str] = field(default_factory=list)
    season_fit: str = "四季"
    score: int = 0
    score_breakdown: dict = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    references: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "tags": self.style_tags,
            "season": self.season_fit,
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "suggestions": self.suggestions,
            "refs": self.references,
        }

    @classmethod
    def empty(cls) -> "OutfitAnalysis":
        return cls()
