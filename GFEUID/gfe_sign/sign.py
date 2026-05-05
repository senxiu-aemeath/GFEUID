"""gfe_sign - 签到/社区/兑换 核心逻辑"""

import json
import time
import logging

from ..utils.gfe_api import (
    sign_in,
    get_task_list,
    get_topic_list,
    view_topic,
    like_topic,
    share_topic,
    get_exchange_list,
    exchange,
)
from ..utils.database.models import GfeUser
from ..gfe_config.gfe_config import GfeConfig

logger = logging.getLogger("gfeuid.gfe_sign")


async def do_sign(user: GfeUser) -> dict:
    """执行签到，返回 {ok, item_name, item_count, exp, score}"""
    try:
        data = await sign_in(user.server, user.web_token)
        await GfeUser.update_sign_time(user.user_id, user.bot_id, int(time.time()))
        return {
            "ok": True,
            "item_name": data.get("itemName", ""),
            "item_count": data.get("itemCount", 0),
            "exp": data.get("exp", 0),
            "score": data.get("score", 0),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def resolve_exchange_items(user: GfeUser) -> list[str]:
    """返回用户的兑换物品ID列表。个人设置优先，空则回退全局默认"""
    raw = user.exchange_items
    if raw and raw != "[]":
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return [str(i) for i in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
    config = GfeConfig.get_config("GfeDefaultExchangeItems")
    if config and hasattr(config, "data") and config.data:
        return [str(i) for i in config.data]
    return []


async def one_click_community(user: GfeUser) -> dict:
    """一键社区：社区任务 → 兑换 → 签到"""
    result = {
        "uid": user.uid,
        "nickname": user.nickname,
        "sign_ok": False,
        "sign_item": "",
        "tasks_done": 0,
        "exchange_done": 0,
        "exchange_items": [],
        "error": None,
    }

    if not user.web_token:
        result["error"] = "未绑定web_token"
        return result

    try:
        # 1. 获取任务列表
        task_data = await get_task_list(user.server, user.web_token)
        daily_tasks = task_data.get("dailyTask", [])

        # 2. 获取帖子列表
        topic_data = await get_topic_list(user.server, user.web_token)
        topic_list = topic_data.get("list", [])
        if not topic_list:
            result["error"] = "获取帖子列表为空"
            return result

        # 3. 执行未完成的每日任务
        tasks_done = 0
        for task in daily_tasks:
            if task.get("status", 0) == 1:
                tasks_done += 1
                continue

            task_type = task.get("task_type", "")
            for topic in topic_list:
                tid = topic.get("topic_id")
                if not tid:
                    continue
                try:
                    if task_type in ("view", "browse"):
                        await view_topic(user.server, user.web_token, tid)
                        tasks_done += 1
                        break
                    elif task_type == "like":
                        await like_topic(user.server, user.web_token, tid)
                        tasks_done += 1
                        break
                    elif task_type == "share":
                        await share_topic(user.server, user.web_token, tid)
                        tasks_done += 1
                        break
                except Exception:
                    continue

        result["tasks_done"] = tasks_done

        # 4. 兑换（如果开启）
        if user.exchange_enable:
            items_to_exchange = resolve_exchange_items(user)
            if items_to_exchange:
                try:
                    exchange_data = await get_exchange_list(user.server, user.web_token)
                    exchange_list = exchange_data.get("list", [])
                    for item in exchange_list:
                        eid = str(item.get("exchange_id", ""))
                        remaining = item.get("max_exchange_count", 0) - item.get("exchange_count", 0)
                        if eid in items_to_exchange and remaining > 0:
                            try:
                                await exchange(user.server, user.web_token, int(eid))
                                result["exchange_done"] += 1
                                result["exchange_items"].append(
                                    item.get("item_name", eid)
                                )
                            except Exception:
                                continue
                except Exception as e:
                    logger.warning(f"[gfe_sign] 兑换流程出错: {e}")

        # 5. 签到
        sign_result = await do_sign(user)
        result["sign_ok"] = sign_result.get("ok", False)
        if result["sign_ok"]:
            result["sign_item"] = sign_result.get("item_name", "")
            result["sign_detail"] = {
                "item_name": sign_result.get("item_name", ""),
                "item_count": sign_result.get("item_count", 0),
                "exp": sign_result.get("exp", 0),
                "score": sign_result.get("score", 0),
            }
        elif not result["error"]:
            result["error"] = sign_result.get("error", "")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[gfe_sign] one_click_community 异常: {e}")

    return result
