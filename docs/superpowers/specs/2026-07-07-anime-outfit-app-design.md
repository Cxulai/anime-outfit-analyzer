# Anime Outfit Analyzer — Design Spec

**Date:** 2026-07-07
**Status:** Draft → Review

## Overview

Windows desktop app (PyQt6). User loads a clothing/fashion photo. App does two things in parallel:
1. Converts photo to anime/manga style via cloud API (multi-style selectable)
2. Analyzes the outfit: identifies each clothing item, tags style, scores the fit, gives 3-5 suggestions

Single user, personal tool. Chinese UI.

## Architecture

Monolithic PyQt6 app with background QThread workers.

```
        ┌──────────────────────────────────┐
        │          PyQt6 MainWindow        │
        │                                  │
        │  ┌──────────┐  ┌──────────┐     │
        │  │ ImagePanel│  │AnimePanel│     │
        │  └──────────┘  └──────────┘     │
        │  ┌──────────────────────────┐   │
        │  │   OutfitAnalysisPanel    │   │
        │  └──────────────────────────┘   │
        └──────────┬───────────────────────┘
                   │ QThread workers (parallel)
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    ┌────────┐ ┌──────┐ ┌──────────┐
    │ Anime  │ │Outfit│ │ Search   │
    │ Worker │ │Worker│ │ Worker   │
    └───┬────┘ └──┬───┘ └────┬─────┘
        │         │           │
   ─ ─ ─│─ ─ ─ ─ ┼ ─ ─ ─ ─ ─│─ ─  network
        ▼         ▼           ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │Replicate│ │ Local  │ │SerpAPI │
   │SD API  │ │CLIP+   │ │or Bing │
   │        │ │YOLOv8  │ │Search  │
   └────────┘ └────────┘ └────────┘
```

## Project Structure

```
anime_outfit_app/
├── main.py              # Entry point
├── ui/
│   ├── main_window.py   # Main window layout
│   ├── image_panel.py   # Original image + drag-drop
│   ├── anime_panel.py   # Anime result display
│   └── outfit_panel.py  # Outfit analysis panel
├── workers/
│   ├── anime_worker.py  # QThread: cloud API call
│   ├── outfit_worker.py # QThread: local model inference
│   └── search_worker.py # QThread: web search
├── models/
│   ├── outfit_model.py  # YOLO + CLIP wrapper
│   ├── anime_client.py  # Replicate API wrapper
│   └── search_client.py # Search API wrapper
├── data/
│   └── schema.py        # Dataclass definitions
├── settings.py           # Config management
├── models_cache/         # Downloaded local models
└── exports/              # Default export folder
```

## UI Layout

```
┌──────────────────────────────────────────────────┐
│  Menu bar                                        │
│  [File ▼]  [Settings ▼]              [Style: ▼] │
├─────────────────┬────────────────────────────────┤
│                 │                                │
│   Original      │    Anime Result                │
│   (drag-drop)   │    (progress while loading)    │
│                 │                                │
├─────────────────┴────────────────────────────────┤
│  Outfit Analysis            Score: ★★★★☆ 7/10   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │ Top    │ │ Bottom │ │ Shoes  │ │ Access │   │
│  │ Name   │ │ Name   │ │ Name   │ │ Name   │   │
│  │ Color  │ │ Color  │ │ Color  │ │ Color  │   │
│  └────────┘ └────────┘ └────────┘ └────────┘   │
│  Suggestions:                                    │
│  • ...                                           │
│  • ...                                           │
│  📎 Reference links: [...]                      │
└──────────────────────────────────────────────────┘
```

**Interactions:**
- Original image: drag-drop + click-to-browse
- Anime style dropdown: 赛璐珞 / 新海诚 / 吉卜力 / 漫画线稿
- Each clothing card clickable for detail
- Bottom: [Export Anime] [Copy Analysis] buttons

## Data Flow

1. User loads image → displayed in left panel
2. User selects style, clicks "Analyze"
3. Three workers start in parallel:
   - **AnimeWorker**: image → Replicate SD img2img with style LoRA → anime result
   - **OutfitWorker**: image → local YOLOv8 segmentation → per-item CLIP classification
   - **SearchWorker**: triggered by OutfitWorker result → search fashion references
4. Each worker result updates UI incrementally
5. All complete → export buttons enabled

## Data Models

```python
@dataclass
class ClothingItem:
    category: str       # 上衣 | 下装 | 鞋子 | 配饰 | 外套
    name: str           # "宽松圆领T恤"
    color: str          # "黑色"
    pattern: str        # 纯色 | 条纹 | 格子 | 碎花 | 迷彩 | ...
    material_hint: str  # 棉质 | 牛仔 | 皮质 | 针织 | ...
    confidence: float   # 0.0 - 1.0

@dataclass
class OutfitAnalysis:
    items: list[ClothingItem]
    style_tags: list[str]       # ["街头休闲", "极简"]
    season_fit: str             # 春夏 | 秋冬 | 四季
    score: int                  # 1-10
    score_breakdown: dict       # {"配色": 7, "比例": 8, "层次": 6, "风格": 7}
    suggestions: list[str]      # 3-5 items
    references: list[str]       # URLs
```

## Outfit Analysis Pipeline

### Detection (YOLOv8)
- Clothing instance segmentation model
- Categories: upper_body, lower_body, full_body(dress), footwear, accessory, outerwear
- If no person/clothing detected → show "未检测到人物或服装"
- If multiple people → analyze the largest person

### Classification (CLIP)
- Per cropped item: predict category, color, pattern, style tags
- Style tag vocabulary: 街头 | 正装 | 休闲 | 运动 | 日系 | 韩系 | 复古 | 极简 | 工装 | 学院 | 波西米亚 | 高街

### Scoring (Rule Engine)

| Dimension | Weight | Logic |
|-----------|--------|-------|
| Color harmony | 30% | Complementary/analogous color matching |
| Proportion | 25% | Top-bottom length ratio (high-waist = bonus) |
| Layering | 20% | ≥3 items without bulk |
| Style consistency | 25% | Tag overlap across items |

Total score = weighted sum, rounded to 1-10.

### Suggestions
- Query: "[item names] 搭配建议" via search API
- Extract summaries + local rule fallback
- Minimum 3, maximum 5 suggestions
- Each suggestion must be specific and actionable

## Anime Conversion

### API: Replicate (replicate.com)
- Model: Stable Diffusion with anime LoRA variants
- Input: original photo, style selection, strength 0.6-0.75
- Output: 1024×1024 anime-styled image

### Style Options → LoRA mapping
| UI Label | LoRA |
|----------|------|
| 赛璐珞风 | anime-lineart-cel-shaded |
| 新海诚风 | makoto-shinkai-style |
| 吉卜力风 | ghibli-studio-style |
| 漫画线稿 | manga-sketch-lineart |

### Error handling
- Timeout (10s) → show error + retry button
- API key invalid/expired → prompt settings
- Rate limited → show wait time + auto-retry once

## Search Integration

### API: SerpAPI or Bing Search API
- Query template: "{item descriptions} 时尚搭配 建议"
- Extract top 3-5 result URLs + snippets
- If search fails → suggestions still generated from local rules, references field empty

## Error Handling Matrix

| Scenario | Behavior |
|----------|----------|
| No person/clothing detected | "未检测到人物或服装，请换一张图" |
| Multiple people | Analyze largest person, note count |
| Low quality (blurry/dark) | Warning toast, still proceed |
| Cloud API timeout/error | Anime panel shows error + retry; outfit analysis unaffected |
| Local model not downloaded | First launch auto-download with progress bar |
| Search API fails | Local suggestions only, references empty |
| Export/save fails | Dialog with reason (permissions/disk full) |

## Settings Page

- Replicate API key
- SerpAPI / Bing Search API key
- Default anime style
- Local model cache path
- Export image format (PNG/JPEG) + quality

## Technical Details

### Local Model Sources
- YOLOv8: `ultralytics` library, auto-downloads pretrained weights from Ultralytics hub
- CLIP: `open-clip-torch` from PyPI, ViT-B/32 checkpoint from Hugging Face (~600MB)
- Both cached in `models_cache/` on first run with download progress bar

### Image Input Constraints
- Accepted formats: JPEG, PNG, WebP, BMP
- Max size: 4096×4096 (auto-resize to 1024px longest edge before processing)
- Min recommended: 512×512 for reliable detection

### "Largest Person" Metric
- YOLO bounding box area (w × h), pick max area

## Key Design Decisions

1. **Monolith over microservices** — single user, simpler deploy, easier to maintain
2. **Local models for outfit** — fast, offline-capable, no per-call cost
3. **Cloud for anime** — Stable Diffusion needs GPU; local SD is heavy for a personal tool
4. **Rule engine for scoring** — simpler than LLM, no API cost, deterministic
5. **Chinese UI only** — personal tool, no i18n needed
6. **YOLOv8 + CLIP** — proven combo for clothing detection/classification
