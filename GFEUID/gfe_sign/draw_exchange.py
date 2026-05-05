"""gfe_sign image renderer — exchange list + exchange result cards."""

import logging

from ..utils.render_utils import render_template, PLAYWRIGHT_AVAILABLE
from ..utils.icon_utils import generate_placeholder_icon, get_status_icon
from ..utils.image import GFE_ACCENT, GFE_BLUE, GFE_RED
from ..utils.database.models import GfeUser

_log = logging.getLogger("gfeuid.gfe_sign.draw")


# Category colors for exchange items (by cycle or type)
_ITEM_COLORS = {
    "daily": GFE_ACCENT,
    "weekly": GFE_BLUE,
    "monthly": GFE_RED,
}


async def draw_exchange_list(
    user: GfeUser,
    exchange_list: list,
    personal_items: list,
    global_items: list,
) -> bytes | None:
    """Render the exchange list as an image card. Returns None on failure."""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        personal_set = set(personal_items)
        global_set = set(global_items)

        items = []
        for item in exchange_list:
            eid = str(item.get("exchange_id", ""))
            name = item.get("item_name", eid)
            score = item.get("use_score", 0)
            total = item.get("max_exchange_count", 0)
            done = item.get("exchange_count", 0)
            remaining = total - done
            cycle = item.get("cycle", "")

            color = _ITEM_COLORS.get(cycle, GFE_ACCENT)
            icon = generate_placeholder_icon(name, color)

            items.append({
                "id": eid,
                "name": name,
                "score": score,
                "remaining": remaining,
                "total": total,
                "cycle": cycle,
                "icon_b64": icon,
                "is_personal": eid in personal_set,
                "is_global": eid not in personal_set and eid in global_set,
            })

        personal_display = ", ".join(personal_items) if personal_items else "(未设置，使用全局)"
        global_display = ", ".join(global_items) if global_items else "(未设置)"

        return await render_template("gfe/sign/exchange_list.html", {
            "nickname": user.nickname or "",
            "uid": user.uid,
            "items": items,
            "personal_display": personal_display,
            "global_display": global_display,
        })
    except Exception:
        _log.warning("draw_exchange_list failed", exc_info=True)
        return None


async def draw_exchange_result(result: dict) -> bytes | None:
    """Render the one-click-community result as an image card."""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        sign_ok = result.get("sign_ok", False)
        sign_detail = result.get("sign_detail") or {}
        error = result.get("error")

        context = {
            "nickname": result.get("nickname", ""),
            "uid": result.get("uid", ""),
            "sign_ok": sign_ok,
            "sign_item": result.get("sign_item", ""),
            "sign_item_count": sign_detail.get("item_count", 0),
            "sign_exp": sign_detail.get("exp", 0),
            "sign_score": sign_detail.get("score", 0),
            "tasks_done": result.get("tasks_done", 0),
            "exchange_done": result.get("exchange_done", 0),
            "exchange_items": result.get("exchange_items", []),
            "error": error,
            "icons": {
                "sign": get_status_icon(sign_ok),
                "task": generate_placeholder_icon("任", (80, 160, 220)),
                "exchange": generate_placeholder_icon("兑", (230, 180, 80)),
                "error": generate_placeholder_icon("!", GFE_RED) if error else "",
            },
        }
        return await render_template("gfe/sign/exchange_result.html", context)
    except Exception:
        _log.warning("draw_exchange_result failed", exc_info=True)
        return None
