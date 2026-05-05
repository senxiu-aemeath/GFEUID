"""Help image renderer."""

import logging

from ..utils.render_utils import render_template, PLAYWRIGHT_AVAILABLE
from ..utils.icon_utils import generate_placeholder_icon
from .help_data import HELP_DATA
from ..version import __version__ as version

_log = logging.getLogger("gfeuid.gfe_help.draw")


async def draw_help_image(prefix: str) -> bytes | None:
    """Render the help command list as an image card. Returns None on failure."""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        categories = []
        for cat in HELP_DATA:
            cat_icon = generate_placeholder_icon(cat["name"], cat["color"], size=28)
            items = []
            for cmd in cat["items"]:
                items.append({
                    "name": cmd["name"],
                    "desc": cmd["desc"],
                    "eg": cmd["eg"].format(prefix=prefix),
                    "icon_b64": generate_placeholder_icon(cmd["name"], cat["color"], size=40),
                })
            categories.append({
                "name": cat["name"],
                "color": cat["color"],
                "icon_b64": cat_icon,
                "items": items,
            })

        return await render_template("gfe/help/help.html", {
            "prefix": prefix,
            "version": version,
            "categories": categories,
        })
    except Exception:
        _log.warning("draw_help_image failed", exc_info=True)
        return None
