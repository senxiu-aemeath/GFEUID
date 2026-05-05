"""GF2 BBS API 封装 — httpx 替代 gf2Api.js"""

import re
from hashlib import md5

import httpx

SERVERS = {
    "cn": {
        "base": "https://gf2-bbs-api.sunborngame.com",
        "origin": "https://gf2-bbs.sunborngame.com",
    },
    "intl": {
        "base": "https://gf2-bbs-api.exiliumgf.com",
        "origin": "https://gf2-bbs.exiliumgf.com",
    },
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
)


def _make_headers(server: str, web_token: str | None = None) -> dict:
    srv = SERVERS.get(server, SERVERS["cn"])
    h = {
        "Content-Type": "application/json",
        "Origin": srv["origin"],
        "Referer": srv["origin"],
        "User-Agent": UA,
    }
    if web_token:
        h["Authorization"] = web_token
    return h


async def _post(server: str, path: str, body: dict | None = None, web_token: str | None = None):
    srv = SERVERS.get(server, SERVERS["cn"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{srv['base']}{path}",
            headers=_make_headers(server, web_token),
            json=body,
        )
        json_data = resp.json()
        if json_data.get("Code") != 0:
            err = RuntimeError(json_data.get("Message", "请求失败"))
            setattr(err, "code", json_data.get("Code"))
            raise err
        return json_data.get("data")


async def _get(server: str, path: str, params: dict | None = None, web_token: str | None = None):
    srv = SERVERS.get(server, SERVERS["cn"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{srv['base']}{path}",
            headers=_make_headers(server, web_token),
            params=params,
        )
        json_data = resp.json()
        if json_data.get("Code") != 0:
            err = RuntimeError(json_data.get("Message", "请求失败"))
            setattr(err, "code", json_data.get("Code"))
            raise err
        return json_data.get("data")


# ── 工具函数 ─────────────────────────────────────────────────

def detect_account_source(account: str) -> str:
    """自动识别账号类型 (phone / mail)，用于密码登录时选择 source 参数"""
    if re.match(r"^1[3-9]\d{9}$", account):
        return "phone"
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", account):
        return "mail"
    err = RuntimeError("账号格式有误，请输入手机号或邮箱")
    setattr(err, "code", "INVALID_ACCOUNT")
    raise err


# ── 登录方式 ─────────────────────────────────────────────────

async def send_sms_code(server: str, account: str):
    """手机号 → 发送短信验证码"""
    await _post(server, "/login/send_msg", {"account_name": account, "graph_code": ""})


async def login_by_sms(server: str, account: str, code: str) -> str:
    """手机号 + 短信验证码 → webToken"""
    data = await _post(server, "/login/sms", {
        "account_name": account,
        "code": code,
        "graph_code": "",
        "source": "phone",
    })
    return data["account"]["token"]


async def login_by_password(server: str, account: str, password: str) -> str:
    """手机号/邮箱 + 密码 → webToken（密码已做 MD5）"""
    source = detect_account_source(account)
    data = await _post(server, "/login/account", {
        "account_name": account,
        "passwd": md5(password.encode()).hexdigest(),
        "source": source,
    })
    return data["account"]["token"]


# ── 用户信息 ─────────────────────────────────────────────────

async def get_user_info(server: str, web_token: str) -> dict:
    """获取用户基本信息（昵称、UID等）"""
    data = await _post(server, "/community/member/info", {"uid": 0}, web_token)
    user = data.get("user", {})
    return {
        "uid": str(user.get("game_uid", "")),
        "nickname": user.get("game_nick_name") or user.get("nick_name", ""),
        "score": user.get("score", 0),
        "level": user.get("level", 0),
    }


# ── 签到 ─────────────────────────────────────────────────────

async def sign_in(server: str, web_token: str) -> dict:
    """签到 → {itemName, itemCount, exp, score}"""
    return await _post(server, "/community/task/sign_in", None, web_token)


# ── 社区任务 ──────────────────────────────────────────────────

async def get_task_list(server: str, web_token: str) -> dict:
    """获取当前任务列表 → {dailyTask, moreTask}"""
    return await _get(server, "/community/task/get_current_task_list", None, web_token)


async def get_topic_list(server: str, web_token: str) -> dict:
    """获取最新帖子列表 → {list: [...]}"""
    return await _get(server, "/community/topic/list", {
        "last_tid": 0,
        "pub_time": 0,
        "reply_time": 0,
        "hot_value": 0,
        "sort_type": 2,
        "category_id": 5,
        "query_type": 1,
    }, web_token)


async def view_topic(server: str, web_token: str, topic_id: str | int):
    """浏览帖子"""
    await _get(server, f"/community/topic/{topic_id}", {"id": str(topic_id)}, web_token)


async def like_topic(server: str, web_token: str, topic_id: str | int):
    """点赞帖子"""
    await _get(server, f"/community/topic/like/{topic_id}", {"id": str(topic_id)}, web_token)


async def share_topic(server: str, web_token: str, topic_id: str | int):
    """分享帖子"""
    await _get(server, f"/community/topic/share/{topic_id}", {"id": str(topic_id)}, web_token)


# ── 兑换 ─────────────────────────────────────────────────────

async def get_exchange_list(server: str, web_token: str) -> dict:
    """获取可兑换物品列表 → {list: [...]}"""
    return await _get(server, "/community/item/exchange_list", None, web_token)


async def exchange(server: str, web_token: str, exchange_id: int):
    """执行兑换"""
    await _post(server, "/community/item/exchange", {"exchange_id": exchange_id}, web_token)
