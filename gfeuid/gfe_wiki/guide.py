"""攻略图片渲染 — 从本地 guide/ 目录读取图片"""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from gsuid_core.logger import logger

from ..gfe_config.gfe_config import GfeConfig
from ..utils.resource.RESOURCE_PATH import GUIDE_PATH


def _compress_to_jpg(img: Image.Image, max_mb: int) -> bytes:
    """转为 JPG，若超过 max_mb 则逐步降低质量"""
    max_bytes = max_mb * 1024 * 1024

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    result = buf.getvalue()
    if len(result) <= max_bytes:
        return result

    for quality in range(90, 10, -5):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        result = buf.getvalue()
        if len(result) <= max_bytes:
            return result
    return result


async def get_guide_images(char_name: str) -> list:
    """获取角色的攻略图片列表 (base64 字符串)"""
    imgs = []
    char_dir = GUIDE_PATH / char_name
    if not char_dir.is_dir():
        return imgs

    max_mb = GfeConfig.get_config("GfeGuideMaxSize").data or 5

    for file in sorted(char_dir.iterdir()):
        if not file.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        try:
            img = Image.open(file)
            img_bytes = _compress_to_jpg(img, max_mb)
            img_b64 = "base64://" + base64.b64encode(img_bytes).decode()
            imgs.append(img_b64)
        except Exception as e:
            logger.warning(f"[GFEuid] 攻略图片读取失败 {file}: {e}")

    return imgs
