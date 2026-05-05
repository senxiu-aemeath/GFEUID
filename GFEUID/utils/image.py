"""PIL 图片工具"""

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BLACK_G = (40, 40, 40)
GREY = (216, 216, 216)
YELLOW = (255, 200, 1)
RED = (255, 0, 0)
GOLD = (224, 202, 146)
WHITE = (255, 255, 255)

# GF2 主题色 — 深色军事风
GFE_DARK = (24, 26, 32)
GFE_ACCENT = (230, 180, 80)
GFE_RED = (210, 60, 50)
GFE_BLUE = (50, 150, 220)


def pil_to_b64(img: Image.Image, quality: int = 0) -> str:
    """PIL Image → base64 data URL。quality=0: PNG；quality>0: WebP"""
    buf = BytesIO()
    if quality > 0:
        img.save(buf, format="WEBP", quality=quality)
        return "base64://" + base64.b64encode(buf.getvalue()).decode()
    img.save(buf, format="PNG")
    return "base64://" + base64.b64encode(buf.getvalue()).decode()


def img_to_b64(path: Union[str, Path], quality: int = 0) -> str:
    """文件路径 → base64 data URL"""
    path = Path(path)
    if not path.exists():
        return ""
    ext = path.suffix.lstrip(".").lower()
    if quality > 0:
        img = Image.open(path).convert("RGBA")
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality)
        return "base64://" + base64.b64encode(buf.getvalue()).decode()
    with open(path, "rb") as f:
        mime = "jpeg" if ext == "jpg" else ext
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill=None,
    outline=None,
):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def get_font(size: int, font_path: Optional[str] = None) -> ImageFont.FreeTypeFont:
    """获取字体，优先指定路径，否则 fallback 到默认"""
    if font_path and Path(font_path).exists():
        return ImageFont.truetype(font_path, size)
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", size)
    except (OSError, IOError):
        pass
    try:
        return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", size)
    except (OSError, IOError):
        pass
    return ImageFont.load_default()
