"""Local anime conversion — Stable Diffusion img2img on GPU."""
import logging
from pathlib import Path

import torch
import numpy as np
from PIL import Image

from settings import get as get_setting

logger = logging.getLogger(__name__)

# Style → (prompt, strength)
STYLE_CONFIG = {
    "赛璐珞风": {
        "prompt": (
            "anime style, cel shaded, flat colors, clean bold outlines, "
            "animation keyframe, high quality anime illustration, vibrant, "
            "preserve original clothing and pose"
        ),
        "negative": "photorealistic, 3d render, blurry, low quality, deformed, bad anatomy",
        "strength": 0.55,
        "steps": 4,
        "guidance": 2.0,
    },
    "新海诚风": {
        "prompt": (
            "Makoto Shinkai anime style, beautiful cinematic lighting, detailed sky, "
            "vibrant painterly background, high quality anime movie frame, "
            "preserve original clothing and pose, soft colors"
        ),
        "negative": "photorealistic, 3d render, dark, low quality, deformed, bad anatomy",
        "strength": 0.60,
        "steps": 4,
        "guidance": 2.0,
    },
    "吉卜力风": {
        "prompt": (
            "Studio Ghibli style, hand-drawn animation, soft watercolor textures, "
            "warm nostalgic colors, Miyazaki aesthetic, preserve original clothing and pose, "
            "gentle lighting"
        ),
        "negative": "photorealistic, 3d render, dark, cgi, low quality, deformed",
        "strength": 0.60,
        "steps": 4,
        "guidance": 2.0,
    },
    "漫画线稿": {
        "prompt": (
            "manga sketch style, black and white line art, hatching, screentone, "
            "ink drawing, comic panel aesthetic, bold strokes, "
            "preserve original clothing and pose, monochrome"
        ),
        "negative": "color, photorealistic, 3d render, blurry, low quality",
        "strength": 0.65,
        "steps": 4,
        "guidance": 2.0,
    },
}

DEFAULT_STYLE = "赛璐珞风"
MODEL_ID = "stabilityai/sd-turbo"
MAX_SIZE = 512  # sd-turbo native resolution


class AnimeLocal:
    """Local Stable Diffusion img2img for anime conversion. GPU required."""

    def __init__(self):
        self._pipe = None
        self._loaded = False
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def ensure_loaded(self):
        if self._loaded:
            return True
        if self._device != "cuda":
            raise RuntimeError("本地 SD 需要 GPU，未检测到 CUDA")

        try:
            from diffusers import AutoPipelineForImage2Image

            logger.info(f"Loading {MODEL_ID} (first run downloads ~2.5GB)...")
            self._pipe = AutoPipelineForImage2Image.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float16,
                variant="fp16",
                safety_checker=None,
            )
            self._pipe.to(self._device)
            # Disable progress bars
            self._pipe.set_progress_bar_config(disable=True)
            self._loaded = True
            logger.info(f"SD Turbo ready on {self._device}")
            return True

        except Exception as e:
            logger.error(f"SD Turbo load failed: {e}")
            self._loaded = False
            raise RuntimeError(f"本地动漫模型加载失败: {e}")

    def convert(self, image_path: str | Path, style: str = DEFAULT_STYLE) -> Image.Image:
        self.ensure_loaded()
        config = STYLE_CONFIG.get(style, STYLE_CONFIG[DEFAULT_STYLE])

        img = Image.open(image_path).convert("RGB")
        orig_size = img.size

        # Resize to model's native resolution
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)

        with torch.no_grad():
            result = self._pipe(
                prompt=config["prompt"],
                negative_prompt=config["negative"],
                image=img,
                strength=config["strength"],
                num_inference_steps=config["steps"],
                guidance_scale=config["guidance"],
            ).images[0]

        # Resize back to original
        if result.size != orig_size:
            result = result.resize(orig_size, Image.LANCZOS)

        return result
