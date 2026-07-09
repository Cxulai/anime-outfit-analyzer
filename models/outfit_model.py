"""Outfit detection & classification — YOLO + CLIP with clothing region bboxes."""
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from data.schema import ClothingItem, OutfitAnalysis
from settings import get as get_setting

logger = logging.getLogger(__name__)

# ── CLIP prompts ──

CATEGORY_PROMPTS = [
    ("上衣", "一件上衣，如T恤、衬衫、卫衣"),
    ("下装", "一条裤子或裙子"),
    ("鞋子", "一双鞋"),
    ("外套", "一件外套、夹克或大衣"),
    ("配饰", "配饰，如项链、手表、帽子、眼镜"),
    ("连衣裙", "一条连衣裙"),
]

COLOR_PROMPTS = [
    "黑色", "白色", "灰色", "红色", "蓝色", "绿色", "黄色",
    "粉色", "紫色", "棕色", "米色", "卡其色", "藏青色", "橙色",
    "银色", "金色", "酒红色", "军绿色",
]

PATTERN_PROMPTS = [
    "纯色", "条纹", "格子", "碎花", "迷彩", "波点", "豹纹", "扎染", "拼接",
]

STYLE_PROMPTS = [
    "街头风格穿搭", "正装风格穿搭", "休闲风格穿搭", "运动风格穿搭",
    "日系风格穿搭", "韩系风格穿搭", "复古风格穿搭", "极简风格穿搭",
    "工装风格穿搭", "学院风格穿搭", "波西米亚风格穿搭", "高街风格穿搭",
]

SEASON_PROMPTS = ["春夏穿搭", "秋冬穿搭", "四季通用穿搭"]

# Body proportion heuristics for clothing region estimation
# (start_ratio, end_ratio) relative to person height
REGION_RATIOS = {
    "上衣": (0.22, 0.52),
    "下装": (0.48, 0.85),
    "鞋子": (0.82, 1.02),
    "外套": (0.18, 0.60),
    "连衣裙": (0.22, 0.82),
    "配饰": (0.05, 0.25),  # head area for hats/glasses/necklaces
}


class OutfitModel:
    """Wraps YOLO person detector + CLIP attribute classifier + region detector."""

    def __init__(self):
        self._yolo = None
        self._clip_model = None
        self._clip_preprocess = None
        self._clip_tokenizer = None
        self._device = "cpu"
        self._loaded = False

    # ── public API ──

    def ensure_loaded(self) -> bool:
        if self._loaded:
            return True
        try:
            self._load_yolo()
            self._load_clip()
            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return False

    def analyze(self, image_path: str | Path) -> OutfitAnalysis:
        if not self._loaded:
            if not self.ensure_loaded():
                return OutfitAnalysis.empty()

        image = Image.open(image_path).convert("RGB")
        orig_w, orig_h = image.size

        # Step 1: detect person
        person_crop, person_bbox = self._detect_largest_person(image)
        if person_crop is None:
            logger.warning("No person detected")
            return OutfitAnalysis.empty()

        # Step 2: detect clothing regions with bounding boxes
        items = self._detect_clothing_regions(person_crop, person_bbox)

        # Step 3: classify each item
        for item in items:
            px1, py1, px2, py2 = item.bbox
            # Crop the region from original image
            region = image.crop((px1, py1, px2, py2))
            if region.width > 10 and region.height > 10:
                item.name, _ = self._classify_name(region, item.category)
                item.color, _ = self._classify_color(region)
                item.pattern, _ = self._classify_pattern(region)

        # Step 4: style tags + season on full person crop
        style_tags = self._classify_style(person_crop)
        season = self._classify_season(person_crop)

        # Step 5: score
        score, breakdown = self._compute_score(items, style_tags)

        return OutfitAnalysis(
            items=items,
            style_tags=style_tags,
            season_fit=season,
            score=score,
            score_breakdown=breakdown,
        )

    # ── model loading ──

    def _load_yolo(self):
        from ultralytics import YOLO
        cache_dir = Path(get_setting("model_cache_dir") or "models_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / "yolov8n.pt"
        self._yolo = YOLO(str(model_path))
        logger.info("YOLOv8n loaded")

    def _load_clip(self):
        import open_clip
        import torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = "ViT-B-32"
        pretrained = "laion2b_s34b_b79k"
        self._clip_model, _, self._clip_preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self._clip_model.to(self._device)
        self._clip_model.eval()
        self._clip_tokenizer = open_clip.get_tokenizer(model_name)
        logger.info(f"CLIP {model_name} loaded on {self._device}")

    # ── person detection ──

    def _detect_largest_person(self, image: Image.Image):
        results = self._yolo(image, classes=[0], verbose=False)
        detections = results[0].boxes

        if detections is None or len(detections) == 0:
            return None, None

        boxes = detections.xyxy.cpu().numpy()
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        idx = int(areas.argmax())
        best = boxes[idx]

        x1, y1, x2, y2 = best.astype(int)
        w, h = x2 - x1, y2 - y1
        pad_w, pad_h = int(w * 0.1), int(h * 0.1)
        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)
        x2 = min(image.width, x2 + pad_w)
        y2 = min(image.height, y2 + pad_h)

        crop = image.crop((x1, y1, x2, y2))
        logger.info(f"Person: bbox={x1},{y1},{x2},{y2}")
        return crop, (x1, y1, x2, y2)

    # ── clothing region detection ──

    def _detect_clothing_regions(self, person_crop: Image.Image, person_bbox: tuple) -> list[ClothingItem]:
        """Detect clothing regions on the person crop, map bboxes to original image coords."""
        px, py, _, _ = person_bbox  # offset of person crop in original image
        pw, ph = person_crop.size

        items = []
        cat_names = [p[0] for p in CATEGORY_PROMPTS]
        cat_prompts = [p[1] for p in CATEGORY_PROMPTS]
        probs = self._clip_probs(person_crop, cat_prompts)

        scored_cats = sorted(
            [(cat_names[i], probs[i]) for i in range(len(cat_names))],
            key=lambda x: x[1], reverse=True
        )

        seen = set()
        for cat_name, cat_conf in scored_cats[:4]:
            if cat_conf < 0.08 or cat_name in seen:
                continue
            seen.add(cat_name)

            # Estimate region using body proportions
            ratios = REGION_RATIOS.get(cat_name, (0.2, 0.6))
            ry1 = int(ratios[0] * ph)
            ry2 = int(ratios[1] * ph)
            rx1 = int(pw * 0.05)
            rx2 = int(pw * 0.95)

            # Map to original image coordinates
            ox1 = px + rx1
            oy1 = py + ry1
            ox2 = px + rx2
            oy2 = py + ry2

            item = ClothingItem(
                category=cat_name,
                name=cat_name,
                color="",
                confidence=round(cat_conf, 3),
                bbox=(ox1, oy1, ox2, oy2),
            )
            items.append(item)

        return items

    # ── CLIP helpers ──

    def _clip_probs(self, image: Image.Image, prompts: list[str]) -> list[float]:
        import torch
        img_tensor = self._clip_preprocess(image).unsqueeze(0).to(self._device)
        text_tokens = self._clip_tokenizer(prompts).to(self._device)

        with torch.no_grad():
            img_feat = self._clip_model.encode_image(img_tensor)
            txt_feat = self._clip_model.encode_text(text_tokens)
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
            txt_feat = txt_feat / txt_feat.norm(dim=-1, keepdim=True)
            logits = (img_feat @ txt_feat.T) * 100.0

        probs = logits.softmax(dim=-1).squeeze(0).tolist()
        return probs

    def _classify_best(self, image: Image.Image, prompts: list[str], threshold: float = 0.0) -> tuple[str, float]:
        probs = self._clip_probs(image, prompts)
        best_idx = int(np.argmax(probs))
        conf = probs[best_idx]
        if conf < threshold:
            return "", conf
        return prompts[best_idx], conf

    def _classify_name(self, image: Image.Image, category: str) -> tuple[str, float]:
        name_prompts = {
            "上衣": ["T恤", "衬衫", "卫衣", "毛衣", "Polo衫", "吊带", "背心", "针织衫", "西装", "短袖"],
            "下装": ["牛仔裤", "休闲裤", "西裤", "短裤", "短裙", "长裙", "运动裤", "阔腿裤"],
            "鞋子": ["运动鞋", "帆布鞋", "皮鞋", "靴子", "凉鞋", "高跟鞋", "板鞋", "拖鞋"],
            "外套": ["牛仔夹克", "西装外套", "风衣", "羽绒服", "棒球服", "针织开衫", "皮夹克"],
            "配饰": ["项链", "手表", "帽子", "眼镜", "耳环", "手链", "围巾", "腰带"],
            "连衣裙": ["碎花连衣裙", "纯色连衣裙", "衬衫裙", "吊带裙", "针织裙"],
        }
        prompts = name_prompts.get(category, ["未知"])
        return self._classify_best(image, prompts)

    def _classify_color(self, image: Image.Image) -> tuple[str, float]:
        return self._classify_best(image, COLOR_PROMPTS)

    def _classify_pattern(self, image: Image.Image) -> tuple[str, float]:
        return self._classify_best(image, PATTERN_PROMPTS)

    def _classify_style(self, person_crop: Image.Image) -> list[str]:
        probs = self._clip_probs(person_crop, STYLE_PROMPTS)
        style_names = [s.replace("风格穿搭", "").replace("穿搭", "") for s in STYLE_PROMPTS]
        scored = sorted(zip(style_names, probs), key=lambda x: x[1], reverse=True)
        return [name for name, conf in scored[:3] if conf > 0.12][:2] or ["休闲"]

    def _classify_season(self, person_crop: Image.Image) -> str:
        name, _ = self._classify_best(person_crop, SEASON_PROMPTS)
        mapping = {"春夏穿搭": "春夏", "秋冬穿搭": "秋冬", "四季通用穿搭": "四季"}
        return mapping.get(name, "四季")

    # ── scoring ──

    def _compute_score(self, items: list[ClothingItem], style_tags: list[str]) -> tuple[int, dict]:
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
