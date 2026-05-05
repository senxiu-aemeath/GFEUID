"""gfe_wiki - Wiki/攻略查询模块"""

import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .draw_doll import draw_doll_wiki
from .draw_weapon import draw_weapon_wiki
from .guide import get_guide_images
from ..gfe_config import PREFIX

sv_gfe_wiki = SV("GFE攻略", priority=10)

# wiki 数据缓存（内存中，首次加载后常驻）
_wiki_dolls: dict[str, str] | None = None  # {slug: name}
_wiki_weapons: dict[str, str] | None = None  # {slug: name}


async def _get_wiki_dolls() -> dict[str, str]:
    global _wiki_dolls
    if _wiki_dolls is not None:
        return _wiki_dolls
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://gf2.mcc.wiki/doll",
                headers={"User-Agent": "Mozilla/5.0 (compatible; gfeuid/0.1)"},
                timeout=30,
            )
            html = resp.text
        dolls = {}
        for m in re.finditer(
            r'href="/doll/([A-Za-z0-9]+)".*?class="flex justify-center items-center bg-white rounded-b">(.*?)</div>',
            html,
            re.DOTALL,
        ):
            dolls[m.group(1)] = m.group(2).strip()
        _wiki_dolls = dolls
        return dolls
    except Exception:
        return {}


async def _get_wiki_weapons() -> dict[str, str]:
    global _wiki_weapons
    if _wiki_weapons is not None:
        return _wiki_weapons
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://gf2.mcc.wiki/weapon",
                headers={"User-Agent": "Mozilla/5.0 (compatible; gfeuid/0.1)"},
                timeout=30,
            )
            html = resp.text
        weapons = {}
        for m in re.finditer(
            r'href="/weapon/(Weapon_[A-Za-z0-9_\-]+_5)".*?class="flex justify-center items-center bg-white rounded-b">(.*?)</div>',
            html,
            re.DOTALL,
        ):
            weapons[m.group(1)] = m.group(2).strip()
        _wiki_weapons = weapons
        return weapons
    except Exception:
        return {}


def _find_doll(name: str, dolls: dict[str, str]) -> tuple | None:
    """模糊匹配角色，返回 (slug, name) 或 None"""
    lower = name.lower()
    for slug, cn in dolls.items():
        if cn == name or slug.lower() == lower:
            return slug, cn
    for slug, cn in dolls.items():
        if cn.lower() == lower:
            return slug, cn
    for slug, cn in dolls.items():
        if cn in name or name in cn or slug.lower() in lower or lower in slug.lower():
            return slug, cn
    return None


def _find_weapon(name: str, weapons: dict[str, str]) -> tuple | None:
    lower = name.lower()
    for slug, cn in weapons.items():
        if cn == name or slug.lower() == lower:
            return slug, cn
    for slug, cn in weapons.items():
        if cn.lower() == lower:
            return slug, cn
    for slug, cn in weapons.items():
        if cn in name or name in cn or slug.lower() in lower or lower in slug.lower():
            return slug, cn
    return None


# ── 角色 Wiki 查询：gfe<角色名>技能/命座/wiki/介绍/图鉴 ────

@sv_gfe_wiki.on_regex(
    rf"^(?P<char>[^技能命座wiki介绍图鉴jn mzj]+)(?:技能|jn|命座|mz|wiki|介绍|圖鑑|图鉴|jieshao|jies)?$",
    block=True,
)
async def send_doll_wiki(bot: Bot, ev: Event):
    char_name = (ev.regex_dict.get("char", "") if hasattr(ev, "regex_dict") else "").strip()
    if not char_name:
        return

    dolls = await _get_wiki_dolls()
    found = _find_doll(char_name, dolls)
    if not found:
        await bot.send(f"[GF2] 未找到角色「{char_name}」，请检查角色名", at_sender=True if ev.group_id else False)
        return

    slug, name = found
    await bot.send(f"[GF2] 正在加载 {name} 的 Wiki...", at_sender=True if ev.group_id else False)
    img = await draw_doll_wiki(slug, name)
    if img:
        await bot.send(MessageSegment.image(img))
    else:
        await bot.send(f"[GF2] 角色「{name}」Wiki 渲染失败\n请访问 https://gf2.mcc.wiki/doll/{slug}")


# ── 武器 Wiki 查询：gfe<武器名>武器 ────────────────────────

@sv_gfe_wiki.on_regex(
    rf"^(?P<weapon>.+)武器$",
    block=True,
)
async def send_weapon_wiki(bot: Bot, ev: Event):
    weapon_input = (ev.regex_dict.get("weapon", "") if hasattr(ev, "regex_dict") else "").strip()
    if not weapon_input:
        return

    weapons = await _get_wiki_weapons()
    found = _find_weapon(weapon_input, weapons)
    if not found:
        # 先尝试角色名→专武
        dolls = await _get_wiki_dolls()
        doll_found = _find_doll(weapon_input, dolls)
        if doll_found:
            await bot.send(
                f"[GF2] 「{weapon_input}」是角色，请用 gfe{weapon_input} 查询",
                at_sender=True if ev.group_id else False,
            )
            return
        await bot.send(f"[GF2] 未找到武器「{weapon_input}」，请检查武器名", at_sender=True if ev.group_id else False)
        return

    slug, name = found
    await bot.send(f"[GF2] 正在加载 {name} 的 Wiki...")
    img = await draw_weapon_wiki(slug, name)
    if img:
        await bot.send(MessageSegment.image(img))
    else:
        await bot.send(f"[GF2] 武器「{name}」Wiki 渲染失败\n请访问 https://gf2.mcc.wiki/weapon/{slug}")


# ── 攻略查询：gfe<角色名>攻略 ──────────────────────────────

@sv_gfe_wiki.on_regex(
    rf"^(?P<char>.+?)(?:攻略|gl|guide)$",
    block=True,
)
async def send_guide(bot: Bot, ev: Event):
    char_name = (ev.regex_dict.get("char", "") if hasattr(ev, "regex_dict") else "").strip()
    if not char_name:
        return

    dolls = await _get_wiki_dolls()
    found = _find_doll(char_name, dolls)
    formal_name = found[1] if found else char_name

    imgs = await get_guide_images(formal_name)
    if not imgs:
        await bot.send(f"[GF2] 未找到「{formal_name}」的攻略图片\n请在 data/GFEUID/guide/{formal_name}/ 目录下放入攻略图片")
        return

    for img in imgs:
        await bot.send(MessageSegment.image(img))


# ── 列表 ─────────────────────────────────────────────────

@sv_gfe_wiki.on_fullmatch(
    ("角色列表", "角色一览", "dolls"),
    block=True,
)
async def send_doll_list(bot: Bot, ev: Event):
    dolls = await _get_wiki_dolls()
    if not dolls:
        await bot.send("[GF2] 获取角色列表失败，请稍后再试")
        return
    names = list(dolls.values())
    names.sort()
    lines = [f"GF2 角色列表（共 {len(names)} 位）", ""]
    for i in range(0, len(names), 4):
        lines.append("  ".join(names[i:i+4]))
    await bot.send("\n".join(lines))


@sv_gfe_wiki.on_fullmatch(
    ("武器列表", "武器一览", "weapons"),
    block=True,
)
async def send_weapon_list(bot: Bot, ev: Event):
    weapons = await _get_wiki_weapons()
    if not weapons:
        await bot.send("[GF2] 获取武器列表失败，请稍后再试")
        return
    names = list(weapons.values())
    names.sort()
    lines = [f"GF2 五星武器列表（共 {len(names)} 把）", ""]
    for i in range(0, len(names), 4):
        lines.append("  ".join(names[i:i+4]))
    await bot.send("\n".join(lines))


# ── Master：刷新缓存 ─────────────────────────────────────

@sv_gfe_wiki.on_fullmatch(
    ("刷新wiki", "清除wiki缓存"),
    block=True,
)
async def refresh_wiki(bot: Bot, ev: Event):
    from gsuid_core.config import core_config
    config_masters = core_config.get_config("masters") or []
    if str(ev.user_id) not in config_masters:
        await bot.send(f"[GF2] 仅 Bot 主人可使用此命令")
        return
    global _wiki_dolls, _wiki_weapons
    _wiki_dolls = None
    _wiki_weapons = None
    from ..utils.resource.RESOURCE_PATH import WIKI_CACHE_PATH
    import shutil
    if WIKI_CACHE_PATH.exists():
        count = len(list(WIKI_CACHE_PATH.iterdir()))
        shutil.rmtree(WIKI_CACHE_PATH)
        WIKI_CACHE_PATH.mkdir(parents=True, exist_ok=True)
    else:
        count = 0
    await bot.send(f"[GF2] Wiki 数据缓存已清除（{count} 个渲染缓存文件）\n下次查询将重新获取数据")
