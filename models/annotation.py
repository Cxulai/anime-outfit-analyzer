"""Annotate anime image with clothing region boxes + arrows + labels + crop extraction."""
from PIL import Image, ImageDraw, ImageFont
import io


# Color palette for clothing categories
CATEGORY_COLORS = {
    "上衣": "#f38ba8",   # pink
    "下装": "#89b4fa",   # blue
    "鞋子": "#a6e3a1",   # green
    "外套": "#fab387",   # orange
    "配饰": "#cba6f7",   # purple
    "连衣裙": "#f9e2af", # yellow
}
DEFAULT_COLOR = "#94e2d5"


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def annotate_image(
    image: Image.Image,
    items: list[dict],
    line_width: int = 3,
) -> Image.Image:
    """
    Draw bounding boxes + labels + connector lines on the image.

    Args:
        image: PIL Image (anime result)
        items: list of item dicts with 'name', 'color', 'category', 'bbox'
        line_width: thickness of annotation lines

    Returns:
        Annotated PIL Image
    """
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    w, h = image.size

    # Try to use a readable font, fall back to default
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size=18)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size=14)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    for i, item in enumerate(items):
        bbox = item.get("bbox", (0, 0, 0, 0))
        x1, y1, x2, y2 = bbox
        if x2 - x1 < 5 or y2 - y1 < 5:
            continue

        cat = item.get("category", "")
        name = item.get("name", "")
        color_name = item.get("color", "")
        hex_color = CATEGORY_COLORS.get(cat, DEFAULT_COLOR)
        rgb = _hex_to_rgb(hex_color)

        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=rgb, width=line_width)

        # Draw corner accents
        corner_len = min(15, (x2 - x1) // 4, (y2 - y1) // 4)
        for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=rgb)

        # Label with connector line
        label = f"{name}"
        if color_name and color_name != "—":
            label += f" ({color_name})"

        # Position label to the right of bbox
        label_x = x2 + 12
        label_y = y1 + (y2 - y1) // 2 - 10

        # If label would go off-screen, put it inside
        if label_x + 120 > w:
            label_x = x1 + 8
        if label_y < 5:
            label_y = 5

        # Connector dot + line
        mid_right = (x2, y1 + (y2 - y1) // 2)
        draw.ellipse(
            [mid_right[0] - 3, mid_right[1] - 3, mid_right[0] + 3, mid_right[1] + 3],
            fill=rgb
        )

        # Text background pill
        bbox_text = draw.textbbox((label_x, label_y), label, font=font_sm)
        pad = 4
        draw.rounded_rectangle(
            [bbox_text[0] - pad, bbox_text[1] - pad, bbox_text[2] + pad, bbox_text[3] + pad],
            radius=6,
            fill=rgb,
        )
        draw.text((label_x, label_y), label, fill="#1e1e2e", font=font_sm)

    return annotated


def crop_items(
    image: Image.Image,
    items: list[dict],
    padding: int = 8,
) -> list[Image.Image]:
    """
    Crop each clothing item region from the image.

    Returns list of cropped PIL Images, same length as items.
    """
    crops = []
    for item in items:
        bbox = item.get("bbox", (0, 0, 0, 0))
        x1, y1, x2, y2 = bbox
        if x2 - x1 < 5 or y2 - y1 < 5:
            crops.append(None)
            continue

        # Add padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)

        crop = image.crop((x1, y1, x2, y2))
        crops.append(crop)

    return crops
