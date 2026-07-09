"""Cloud anime conversion — SiliconFlow Qwen-Image API (Chinese payment, Alipay/WeChat)."""
import base64
import json
import logging
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from settings import get as get_setting

logger = logging.getLogger(__name__)

API_URL = "https://api.siliconflow.cn/v1/images/generations"
MODEL_NAME = "Qwen/Qwen-Image-Edit-2509"

# Style → prompt
STYLE_PROMPTS = {
    "赛璐珞风": (
        "Transform this photo into a cel-shaded anime illustration. "
        "Clean flat colors, bold dark outlines, animation keyframe quality. "
        "Preserve the original clothing design, pose, and composition exactly. "
        "Anime style, vibrant, crisp line art."
    ),
    "新海诚风": (
        "Transform this photo into Makoto Shinkai anime movie style. "
        "Beautiful cinematic lighting, detailed sky with soft clouds, "
        "vibrant painterly background, glowing light rays. "
        "Preserve the original clothing, pose, and composition. "
        "Your Name / Weathering With You aesthetic."
    ),
    "吉卜力风": (
        "Transform this photo into Studio Ghibli hand-drawn animation style. "
        "Soft watercolor textures, warm nostalgic colors, gentle lighting. "
        "Miyazaki film aesthetic. Preserve the original clothing and pose. "
        "Spirited Away / Howl's Moving Castle style."
    ),
    "漫画线稿": (
        "Transform this photo into manga sketch style. "
        "Black and white line art, hatching and screentone shading, "
        "bold ink outlines, comic panel aesthetic, monochrome. "
        "Preserve the original clothing, pose, and composition."
    ),
}

DEFAULT_STYLE = "赛璐珞风"
MAX_RETRIES = 2
TIMEOUT = 60


class AnimeClient:
    """Calls SiliconFlow Qwen-Image API for high-quality anime conversion."""

    def _get_headers(self):
        api_key = (get_setting("replicate_api_key") or "").strip()
        if not api_key:
            raise ValueError("请先设置 API Key（设置 > 偏好设置）\n"
                           "在 siliconflow.cn 注册获取免费额度")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def convert(self, image_path: str | Path, style: str = DEFAULT_STYLE) -> Image.Image:
        prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])

        # Read and encode image
        img = Image.open(image_path).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_uri = f"data:image/png;base64,{img_b64}"

        headers = self._get_headers()

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "image": data_uri,
            "image_size": "1024x1024",
            "prompt_enhancement": True,
        }

        logger.info(f"SiliconFlow Qwen-Image (style={style})")

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT)
                data = resp.json()

                if resp.status_code != 200:
                    msg = data.get("message", str(data))
                    if resp.status_code == 401:
                        raise ValueError("API Key 无效，请检查设置")
                    if resp.status_code == 402:
                        raise RuntimeError("余额不足，请在 siliconflow.cn 充值")
                    if resp.status_code == 429:
                        if attempt < MAX_RETRIES:
                            time.sleep(5)
                            continue
                        raise RuntimeError("请求过于频繁")
                    raise RuntimeError(f"API 错误 ({resp.status_code}): {msg}")

                # Parse response: {"images": [{"url": "..."}]} or {"data": [{"url": "..."}]}
                images = data.get("images") or data.get("data") or []
                if not images:
                    raise RuntimeError(f"API 返回无图片: {json.dumps(data, ensure_ascii=False)[:300]}")

                result_url = images[0].get("url") or images[0]
                if isinstance(result_url, dict):
                    result_url = result_url.get("url", "")
                result_url = str(result_url)

                if not result_url or not result_url.startswith("http"):
                    raise RuntimeError(f"无效的图片 URL: {result_url}")

                logger.info(f"Result: {result_url[:100]}...")
                img_resp = requests.get(result_url, timeout=30)
                img_resp.raise_for_status()
                return Image.open(BytesIO(img_resp.content)).convert("RGB")

            except (ValueError, RuntimeError):
                raise
            except requests.Timeout:
                if attempt < MAX_RETRIES:
                    time.sleep(3)
                    continue
                raise RuntimeError("API 请求超时，请重试")
            except Exception as e:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Retry {attempt+1}: {e}")
                    time.sleep(3)
                    continue
                raise RuntimeError(f"动漫化失败: {e}")
        raise RuntimeError("动漫化失败：已达最大重试次数")
