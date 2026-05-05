"""Placeholder icon generator — PIL-generated icons for HTML templates."""

import base64
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw

from .image import get_font, GFE_ACCENT


def pil_to_data_url(img: Image.Image, fmt: str = "PNG") -> str:
    """PIL Image → data:image/...;base64,... for HTML <img src>."""
    buf = BytesIO()
    img.save(buf, format=fmt)
    return "data:image/" + fmt.lower() + ";base64," + base64.b64encode(buf.getvalue()).decode()


def generate_placeholder_icon(
    text: str,
    color: Tuple[int, int, int] = GFE_ACCENT,
    size: int = 64,
) -> str:
    """Generate a rounded-rect icon with colored background and white text.

    Returns a data:image/png;base64,... string ready for <img src>.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = max(size // 8, 4)
    draw.rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=radius,
        fill=color,
    )

    label = text[:2] if len(text) >= 2 else text[:1]
    font_size = size // 2
    font = get_font(font_size)

    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]

    draw.text((x, y), label, fill=(255, 255, 255), font=font)

    return pil_to_data_url(img)


def get_status_icon(ok: bool, size: int = 32) -> str:
    """Return a checkmark (green) or X (red) icon as data URL."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if ok:
        color = (80, 200, 80)
        # checkmark ✓
        label = "✓"
    else:
        color = (210, 60, 50)
        label = "✗"

    radius = max(size // 6, 3)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=color)

    font = get_font(int(size * 0.65))
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), label, fill=(255, 255, 255), font=font)

    return pil_to_data_url(img)
