"""gfe_sign - 自动签到/社区/兑换 模块"""

import json
import time
import logging

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.config import core_config
from gsuid_core.logger import logger
from gsuid_core.aps import scheduler

from .sign import do_sign, one_click_community, resolve_exchange_items
from ..utils.database.models import GfeUser
from ..utils.gfe_api import get_exchange_list as api_get_exchange_list
from ..gfe_config.gfe_config import GfeConfig

sv_gfe_sign = SV("GFE社区", priority=5)
_log = logging.getLogger("gfeuid.gfe_sign")


def _at(ev: Event) -> bool:
    return True if ev.group_id else False


async def _require_user(ev: Event) -> GfeUser | None:
    user = await GfeUser.select_by_user(ev.user_id, ev.bot_id)
    if not user or not user.web_token:
        return None
    return user


# ── 签到 ─────────────────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("签到", "sign"), block=True)
async def cmd_sign(bot: Bot, ev: Event):
    user = await _require_user(ev)
    if not user:
        await bot.send("[GF2] 请先 gfe登录 绑定账号", at_sender=_at(ev))
        return

    await bot.send("[GF2] 正在签到...", at_sender=_at(ev))
    result = await do_sign(user)
    if result["ok"]:
        msg = (
            f"[GF2] 签到成功\n"
            f"▸ 获得: {result['item_name']} x{result['item_count']}\n"
            f"▸ 经验: +{result['exp']}  积分: +{result['score']}"
        )
    else:
        msg = f"[GF2] 签到失败: {result.get('error', '未知错误')}"
    await bot.send(msg, at_sender=_at(ev))


# ── 一键社区 ─────────────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("一键社区", "community"), block=True)
async def cmd_community(bot: Bot, ev: Event):
    user = await _require_user(ev)
    if not user:
        await bot.send("[GF2] 请先 gfe登录 绑定账号", at_sender=_at(ev))
        return

    await bot.send("[GF2] 正在执行一键社区...", at_sender=_at(ev))
    result = await one_click_community(user)

    msgs = [f"[GF2] 一键社区完成 | {result['nickname']}({result['uid']})"]
    if result["sign_ok"]:
        msgs.append(f"▸ 签到: 成功 ({result.get('sign_item', '')})")
    else:
        msgs.append("▸ 签到: 跳过或失败")
    msgs.append(f"▸ 社区任务: 完成 {result['tasks_done']} 项")
    if result["exchange_done"] > 0:
        items = "、".join(result["exchange_items"])
        msgs.append(f"▸ 兑换: 成功 {result['exchange_done']} 件 ({items})")
    if result.get("error"):
        msgs.append(f"▸ 提示: {result['error']}")

    await bot.send("\n".join(msgs), at_sender=_at(ev))


# ── 开启/关闭自动社区 ────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("开启自动社区",), block=True)
async def cmd_auto_community_on(bot: Bot, ev: Event):
    await GfeUser.set_auto_community(ev.user_id, ev.bot_id, True)
    await bot.send("[GF2] 已开启自动社区（每日自动签到+社区+兑换）", at_sender=_at(ev))


@sv_gfe_sign.on_fullmatch(("关闭自动社区",), block=True)
async def cmd_auto_community_off(bot: Bot, ev: Event):
    await GfeUser.set_auto_community(ev.user_id, ev.bot_id, False)
    await bot.send("[GF2] 已关闭自动社区", at_sender=_at(ev))


# ── 开启/关闭自动兑换 ────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("开启自动兑换",), block=True)
async def cmd_exchange_on(bot: Bot, ev: Event):
    await GfeUser.set_exchange_enable(ev.user_id, ev.bot_id, True)
    await bot.send("[GF2] 已开启自动兑换（一键社区时将同时兑换物品）", at_sender=_at(ev))


@sv_gfe_sign.on_fullmatch(("关闭自动兑换",), block=True)
async def cmd_exchange_off(bot: Bot, ev: Event):
    await GfeUser.set_exchange_enable(ev.user_id, ev.bot_id, False)
    await bot.send("[GF2] 已关闭自动兑换", at_sender=_at(ev))


# ── 兑换列表 ─────────────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("兑换列表",), block=True)
async def cmd_exchange_list(bot: Bot, ev: Event):
    user = await _require_user(ev)
    if not user:
        await bot.send("[GF2] 请先 gfe登录 绑定账号", at_sender=_at(ev))
        return

    try:
        data = await api_get_exchange_list(user.server, user.web_token)
        exchange_list = data.get("list", [])
    except Exception as e:
        await bot.send(f"[GF2] 获取兑换列表失败: {e}", at_sender=_at(ev))
        return

    if not exchange_list:
        await bot.send("[GF2] 当前无可兑换物品", at_sender=_at(ev))
        return

    personal_items = resolve_exchange_items(user)
    global_conf = GfeConfig.get_config("GfeDefaultExchangeItems")
    global_items = [str(i) for i in global_conf.data] if global_conf and global_conf.data else []

    lines = ["[GF2] 可兑换物品列表", ""]
    for item in exchange_list:
        eid = str(item.get("exchange_id", ""))
        name = item.get("name", eid)
        stock = item.get("stock", 0)
        score = item.get("score", 0)
        mark = ""
        if eid in personal_items:
            mark = " ★(个人)"
        elif eid in global_items:
            mark = " ☆(全局)"
        lines.append(f"  [{eid}] {name}  |  {score}积分  |  库存:{stock}{mark}")

    personal_display = ", ".join(personal_items) if personal_items else "(未设置，使用全局)"
    global_display = ", ".join(global_items) if global_items else "(未设置)"
    lines.append(f"\n★ 个人兑换: {personal_display}")
    lines.append(f"☆ 全局默认: {global_display}")
    await bot.send("\n".join(lines), at_sender=_at(ev))


# ── 兑换设置 (on_command 支持带/不带参数) ───────────────────

@sv_gfe_sign.on_command(("兑换设置",), block=True)
async def cmd_exchange_set(bot: Bot, ev: Event):
    args = ev.text.strip() if ev.text else ""

    if not args:
        await GfeUser.set_exchange_items(ev.user_id, ev.bot_id, "[]")
        global_conf = GfeConfig.get_config("GfeDefaultExchangeItems")
        if global_conf and global_conf.data:
            await bot.send(
                f"[GF2] 已清除个人兑换设置，将使用全局默认: {', '.join(str(i) for i in global_conf.data)}",
                at_sender=_at(ev),
            )
        else:
            await bot.send("[GF2] 已清除个人兑换设置（全局默认也为空）", at_sender=_at(ev))
        return

    ids = [x.strip() for x in args.split() if x.strip()]
    await GfeUser.set_exchange_items(ev.user_id, ev.bot_id, json.dumps(ids))
    await bot.send(f"[GF2] 已设置个人兑换物品: {', '.join(ids)}", at_sender=_at(ev))


# ── 自动任务状态 ─────────────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("自动任务状态", "我的状态"), block=True)
async def cmd_status(bot: Bot, ev: Event):
    user = await GfeUser.select_by_user(ev.user_id, ev.bot_id)
    if not user:
        await bot.send("[GF2] 请先 gfe登录 绑定账号", at_sender=_at(ev))
        return

    personal_items = resolve_exchange_items(user)
    last_sign = (
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.last_sign_time))
        if user.last_sign_time
        else "从未签到"
    )

    msgs = [
        f"[GF2] 自动任务状态 | {user.nickname}({user.uid})",
        f"▸ 自动社区: {'开启' if user.auto_community else '关闭'}",
        f"▸ 自动兑换: {'开启' if user.exchange_enable else '关闭'}",
        f"▸ 兑换物品: {', '.join(personal_items) if personal_items else '(未设置)'}",
        f"▸ 最后签到: {last_sign}",
    ]
    await bot.send("\n".join(msgs), at_sender=_at(ev))


# ── 全部签到 (master) ───────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("全部签到", "全部sign"), block=True)
async def cmd_sign_all(bot: Bot, ev: Event):
    masters = core_config.get_config("masters") or []
    if str(ev.user_id) not in masters:
        await bot.send("[GF2] 仅 Bot 主人可使用此命令")
        return

    users = await GfeUser.get_all_users_with_token()
    if not users:
        await bot.send("[GF2] 没有已绑定账号的用户")
        return

    await bot.send(f"[GF2] 开始为 {len(users)} 位用户签到...")
    ok = fail = 0
    for user in users:
        result = await do_sign(user)
        if result["ok"]:
            ok += 1
        else:
            fail += 1
            _log.warning(f"全部签到 {user.uid}: {result.get('error')}")

    await bot.send(f"[GF2] 全部签到完成: {ok} 成功 / {fail} 失败 / {len(users)} 总计")


# ── 全部一键社区 (master) ────────────────────────────────────

@sv_gfe_sign.on_fullmatch(("全部一键社区", "全部community"), block=True)
async def cmd_community_all(bot: Bot, ev: Event):
    masters = core_config.get_config("masters") or []
    if str(ev.user_id) not in masters:
        await bot.send("[GF2] 仅 Bot 主人可使用此命令")
        return

    users = await GfeUser.get_all_users_with_token()
    if not users:
        await bot.send("[GF2] 没有已绑定账号的用户")
        return

    await bot.send(f"[GF2] 开始为 {len(users)} 位用户执行一键社区...")
    ok = fail = 0
    for user in users:
        result = await one_click_community(user)
        if result["sign_ok"]:
            ok += 1
        else:
            fail += 1
            _log.warning(f"全部一键社区 {user.uid}: {result.get('error')}")

    await bot.send(f"[GF2] 全部一键社区完成: {ok} 成功 / {fail} 失败 / {len(users)} 总计")


# ── 定时任务 ─────────────────────────────────────────────────

def _parse_cron(expr: str) -> dict:
    """解析5字段cron：分 时 日 月 周 → apscheduler kwargs，* 的字段不传"""
    parts = expr.strip().split()
    if len(parts) != 5:
        _log.warning(f"无效的cron表达式: {expr}，使用默认配置")
        return {"hour": "9", "minute": "0"}
    mapping = ["minute", "hour", "day", "month", "day_of_week"]
    result = {}
    for i, name in enumerate(mapping):
        if parts[i] != "*":
            result[name] = parts[i]
    return result


async def _auto_community_cron():
    if not GfeConfig.get_config("GfeAutoCommunity").data:
        return

    users = await GfeUser.get_all_auto_community_users()
    if not users:
        _log.info("[gfe_sign] 没有开启自动社区的用户，跳过")
        return

    _log.info(f"[gfe_sign] 自动社区开始: {len(users)} 位用户")
    success = fail = 0
    for user in users:
        try:
            result = await one_click_community(user)
            if result["sign_ok"]:
                success += 1
            else:
                fail += 1
                _log.warning(
                    f"[gfe_sign] {user.nickname}({user.uid}) 失败: {result.get('error')}"
                )
        except Exception as e:
            fail += 1
            _log.error(f"[gfe_sign] {user.nickname}({user.uid}) 异常: {e}")

    _log.info(f"[gfe_sign] 自动社区完成: {success}成功/{fail}失败/{len(users)}总计")

    report_group = GfeConfig.get_config("GfeSignReportGroup").data
    if report_group and str(report_group).strip():
        try:
            from gsuid_core.bot import get_bot
            bot = get_bot()
            if bot:
                msg = (
                    f"━━━ GFEuid 自动社区报告 ━━━\n"
                    f"成功: {success}  失败: {fail}  总计: {len(users)}"
                )
                await bot.send_group_msg(group_id=int(report_group), message=msg)
        except Exception as e:
            _log.warning(f"[gfe_sign] 发送群报告失败: {e}")


_cron_expr = GfeConfig.get_config("GfeAutoSignCron").data or "0 9 * * *"
_cron_kwargs = _parse_cron(_cron_expr)


@scheduler.scheduled_job("cron", **_cron_kwargs)
async def scheduled_auto_community():
    await _auto_community_cron()


_log.info(f"[gfe_sign] 模块加载完成，定时任务: {_cron_expr}")
