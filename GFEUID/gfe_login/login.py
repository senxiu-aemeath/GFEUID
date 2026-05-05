"""gfe_login - GF2 网页登录核心逻辑"""

import asyncio
import hashlib
import os
import re
import time
from pathlib import Path

import httpx
from async_timeout import timeout
from pydantic import BaseModel
from starlette.responses import HTMLResponse

from gsuid_core.bot import Bot
from gsuid_core.config import core_config
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.web_app import app

from ..utils.cache import TimedCache
from ..utils.resource.RESOURCE_PATH import MAIN_PATH
from ..utils.gfe_api import (
    send_sms_code,
    login_by_sms,
    login_by_password,
    login_by_game_token,
    get_user_info,
)
from ..utils.database.models import GfeBind, GfeUser
from ..gfe_config.gfe_config import GfeConfig
from ..gfe_config import PREFIX
from ..utils.util import get_public_ip

cache = TimedCache(
    timeout=180,
    maxsize=100,
    persist_path=MAIN_PATH / "url_cache.db",
)


def _get_token(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:8]


async def _get_url() -> tuple[str, bool]:
    url = GfeConfig.get_config("GfeLoginUrl").data
    if url:
        if not url.startswith("http"):
            url = f"https://{url}"
        return url.rstrip("/"), GfeConfig.get_config("GfeLoginUrlSelf").data
    host = core_config.get_config("HOST")
    port = core_config.get_config("PORT")
    if host in ("localhost", "127.0.0.1"):
        actual_host = "localhost"
    else:
        actual_host = await get_public_ip(host)
    return f"http://{actual_host}:{port}", True


async def _send_login_msg(bot: Bot, ev: Event, url: str):
    at_sender = True if ev.group_id else False

    if GfeConfig.get_config("GfeLoginForward").data:
        im = [
            MessageSegment.text(f"[GF2] 您的ID为【{ev.user_id}】\n请点击链接登录 GF2 账号"),
            MessageSegment.text(url),
            MessageSegment.text("3分钟内有效"),
        ]
        if not ev.group_id and ev.bot_id == "onebot":
            await bot.send(f"[GF2] 您的ID为【{ev.user_id}】\n请点击链接登录 GF2 账号\n{url}\n3分钟内有效")
        else:
            await bot.send(MessageSegment.node(im))
    else:
        await bot.send(
            f"[GF2] 您的ID为【{ev.user_id}】\n请点击链接登录 GF2 账号\n{url}\n3分钟内有效",
            at_sender=at_sender,
        )


async def _identify_token(token: str) -> dict:
    """尝试识别 token 类型并验证，返回绑定结果或抛出异常"""
    for srv in ("cn", "intl"):
        # 尝试 1: 直接作为 BBS webToken
        try:
            info = await get_user_info(srv, token)
            if info.get("uid"):
                return {"server": srv, "login_type": "web_token", "info": info, "web_token": token}
        except Exception:
            pass

        # 尝试 2: 作为 game AccessToken 换取 webToken
        try:
            web_token = await login_by_game_token(srv, token)
            info = await get_user_info(srv, web_token)
            if info.get("uid"):
                return {
                    "server": srv,
                    "login_type": "game_token",
                    "info": info,
                    "web_token": web_token,
                    "access_token": token,
                }
        except Exception:
            continue

    raise RuntimeError("Token 无效，请检查后重试")


async def _save_binding(user_id: str, bot_id: str, server: str, login_type: str,
                        web_token: str, info: dict, access_token: str = ""):
    """保存或更新用户绑定数据"""
    common = {
        "user_id": user_id,
        "bot_id": bot_id,
        "uid": info["uid"],
        "nickname": info["nickname"],
        "web_token": web_token,
        "server": server,
        "login_type": login_type,
        "last_bind_time": int(time.time()),
    }

    existing = await GfeUser.select_by_user(user_id, bot_id)
    if existing:
        await GfeUser.update_data(**common)
    else:
        await GfeUser.insert_data(**common)

    await GfeBind.insert_gfe_uid(user_id, bot_id, info["uid"], server)


async def page_login(bot: Bot, ev: Event):
    url, is_local = await _get_url()
    user_token = _get_token(ev.user_id)

    cache.set(user_token, {
        "flow": "login",
        "user_id": ev.user_id,
        "bot_id": ev.bot_id,
        "step": "select_server",
        "server": "",
        "method": "",
        "account": "",
        "code": "",
        "password": "",
    })

    login_url = f"{url}/gfe/i/{user_token}"
    logger.info(f"[GFEuid] 登录 user_id={ev.user_id} token={user_token} url={login_url}")
    await _send_login_msg(bot, ev, login_url)

    at_sender = False
    try:
        async with timeout(180):
            while True:
                result = cache.get(user_token)
                if result is None:
                    return
                if result.get("step") == "done":
                    cache.delete(user_token)
                    break
                await asyncio.sleep(1)
    except asyncio.TimeoutError:
        cache.delete(user_token)
        return await bot.send("[GF2] 登录超时！", at_sender=at_sender)

    server = result.get("server", "cn")
    method = result.get("method", "")
    account = result.get("account", "")
    user_id = result.get("user_id", "")
    login_type = method
    access_token = ""

    try:
        if method == "sms":
            web_token = await login_by_sms(server, account, result.get("code", ""))
        elif method == "password":
            web_token = await login_by_password(server, account, result.get("password", ""))
        elif method == "token":
            token_value = result.get("token_value", "")
            ident = await _identify_token(token_value)
            web_token = ident["web_token"]
            login_type = ident["login_type"]
            access_token = ident.get("access_token", "")
            server = ident["server"]
        else:
            return await bot.send(f"[GF2] 未知登录方式: {method}", at_sender=at_sender)

        info = await get_user_info(server, web_token)
        await _save_binding(user_id, ev.bot_id, server, login_type, web_token, info, access_token)

        server_name = "国服" if server == "cn" else "国际服"
        type_map = {"sms": "短信验证码", "password": "账号密码", "web_token": "WebToken", "game_token": "AccessToken"}
        extra = "  |  已解锁抽卡功能" if login_type == "game_token" else ""
        return await bot.send(
            f"[GF2] 登录绑定成功！\n"
            f"服务器：{server_name}\n"
            f"昵称：{info['nickname']}\n"
            f"UID：{info['uid']}\n"
            f"方式：{type_map.get(login_type, login_type)}{extra}",
            at_sender=at_sender,
        )

    except Exception as e:
        return await bot.send(f"[GF2] 登录失败：{e}", at_sender=at_sender)


# ── FastAPI 路由 ─────────────────────────────────────────────

TEMP_PATH = Path(__file__).parents[1] / "templates"


def _read_template(name: str) -> str:
    path = TEMP_PATH / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<html><body><h1>Template not found</h1></body></html>"


@app.get("/gfe/i/{token}")
async def gfe_login_page(token: str):
    state = cache.get(token)
    if state is None:
        return HTMLResponse(
            _read_template("gfe/login/404.html")
            if (TEMP_PATH / "gfe/login/404.html").exists()
            else "<html><body><h1>登录链接已过期，请重新发送 gfe登录</h1></body></html>"
        )

    html = _read_template("gfe/login/index.html")
    html = html.replace("{{ token }}", token)
    html = html.replace("{{ user_id }}", state.get("user_id", ""))

    # 检查用户是否已有绑定
    user_id = state.get("user_id", "")
    bot_id = state.get("bot_id", "")
    try:
        user = await GfeUser.select_by_user(user_id, bot_id)
        if user and user.web_token:
            server_name = "国服" if user.server == "cn" else "国际服"
            type_map = {"sms": "短信验证码", "password": "账号密码", "web_token": "WebToken", "game_token": "AccessToken"}
            html = html.replace("{{ has_binding }}", "true")
            html = html.replace("{{ bind_nickname }}", user.nickname or "")
            html = html.replace("{{ bind_uid }}", user.uid or "")
            html = html.replace("{{ bind_server }}", server_name)
            html = html.replace("{{ bind_login_type }}", type_map.get(user.login_type, user.login_type or "未知"))
            html = html.replace("{{ bind_has_game_token }}", "true" if user.login_type == "game_token" else "false")
        else:
            html = html.replace("{{ has_binding }}", "false")
            html = html.replace("{{ bind_nickname }}", "")
            html = html.replace("{{ bind_uid }}", "")
            html = html.replace("{{ bind_server }}", "")
            html = html.replace("{{ bind_login_type }}", "")
            html = html.replace("{{ bind_has_game_token }}", "false")
    except Exception:
        html = html.replace("{{ has_binding }}", "false")
        html = html.replace("{{ bind_nickname }}", "")
        html = html.replace("{{ bind_uid }}", "")
        html = html.replace("{{ bind_server }}", "")
        html = html.replace("{{ bind_login_type }}", "")
        html = html.replace("{{ bind_has_game_token }}", "false")

    return HTMLResponse(html)


class SubmitModel(BaseModel):
    token: str
    step: str = ""
    server: str = ""
    method: str = ""
    account: str = ""
    code: str = ""
    password: str = ""
    token_value: str = ""


@app.post("/gfe/submit")
async def gfe_login_submit(data: SubmitModel):
    state = cache.get(data.token)
    if state is None:
        return {"success": False, "msg": "登录超时，请重新发送 gfe登录"}

    step = data.step
    user_id = state.get("user_id", "")
    bot_id = state.get("bot_id", "")

    # ── 删除绑定（已绑定用户在页面操作）──

    if step == "delete_binding":
        try:
            user = await GfeUser.select_by_user(user_id, bot_id)
            if user:
                await GfeUser.delete_user(user_id, bot_id)
            return {"success": True, "msg": "已删除绑定", "reset": True}
        except Exception as e:
            return {"success": False, "msg": f"删除失败: {e}"}

    # ── 升级绑定（已有账号，补充绑定 game token）──

    if step == "upgrade_token":
        token_value = (data.token_value or "").strip()
        if not token_value:
            return {"success": False, "msg": "请输入 Token"}
        try:
            ident = await _identify_token(token_value)
            web_token = ident["web_token"]
            info = ident["info"]
            server = ident["server"]
            login_type = ident["login_type"]
            access_token_val = ident.get("access_token", "")
            await _save_binding(user_id, bot_id, server, login_type, web_token, info, access_token_val)
            type_map = {"web_token": "WebToken", "game_token": "AccessToken"}
            extra = "，已解锁抽卡功能" if login_type == "game_token" else ""
            return {
                "success": True,
                "msg": f"升级成功：{info['nickname']} ({type_map.get(login_type, login_type)}){extra}",
            }
        except Exception as e:
            return {"success": False, "msg": f"Token 验证失败: {e}"}

    # ── 选择服务器 ──

    if step == "select_server":
        if data.server not in ("cn", "intl"):
            return {"success": False, "msg": "请选择有效的服务器"}
        state["server"] = data.server
        state["step"] = "select_method"
        cache.set(data.token, state)
        return {"success": True, "next": "select_method"}

    # ── 选择登录方式 ──

    elif step == "select_method":
        if data.method not in ("sms", "password", "token"):
            return {"success": False, "msg": "请选择有效的登录方式"}
        state["method"] = data.method
        if data.method == "sms":
            state["step"] = "input_account"
            cache.set(data.token, state)
            return {"success": True, "next": "input_account"}
        elif data.method == "token":
            state["step"] = "input_token"
            cache.set(data.token, state)
            return {"success": True, "next": "input_token"}
        else:
            state["step"] = "input_password"
            cache.set(data.token, state)
            return {"success": True, "next": "input_password"}

    # ── 短信 ──

    elif step == "send_sms":
        account = data.account.strip()
        if not re.match(r"^1[3-9]\d{9}$", account):
            return {"success": False, "msg": "请输入有效的11位手机号"}
        state["account"] = account
        try:
            await send_sms_code(state.get("server", "cn"), account)
            state["step"] = "input_code"
            cache.set(data.token, state)
            return {"success": True, "msg": "验证码已发送", "next": "input_code"}
        except Exception as e:
            return {"success": False, "msg": f"发送验证码失败：{e}"}

    elif step == "verify_sms":
        account = state.get("account", "")
        code = data.code.strip()
        if not code:
            return {"success": False, "msg": "请输入验证码"}
        state["code"] = code
        state["step"] = "done"
        cache.set(data.token, state)
        return {"success": True, "msg": "登录成功！请返回聊天窗口查看"}

    # ── 密码 ──

    elif step == "verify_password":
        account = data.account.strip()
        password = data.password
        if not account:
            return {"success": False, "msg": "请输入手机号或邮箱"}
        if not password:
            return {"success": False, "msg": "请输入密码"}
        state["account"] = account
        state["password"] = password
        state["step"] = "done"
        cache.set(data.token, state)
        return {"success": True, "msg": "登录成功！请返回聊天窗口查看"}

    # ── Token 登录 ──

    elif step == "verify_token":
        token_value = (data.token_value or "").strip()
        if not token_value:
            return {"success": False, "msg": "请输入 Token"}
        try:
            ident = await _identify_token(token_value)
            # 将识别结果写入 state，page_login 轮询获取
            state["token_value"] = token_value
            state["server"] = ident["server"]
            state["method"] = "token"  # page_login 根据这个调 _identify_token_async
            state["step"] = "done"
            cache.set(data.token, state)
            type_map = {"web_token": "WebToken", "game_token": "AccessToken"}
            extra = "，可同时用于社区和抽卡记录" if ident["login_type"] == "game_token" else ""
            return {
                "success": True,
                "msg": f"Token 验证成功（{type_map.get(ident['login_type'], ident['login_type'])}）{extra}\n请返回聊天窗口查看",
            }
        except Exception as e:
            return {"success": False, "msg": f"Token 验证失败: {e}"}

    return {"success": False, "msg": "无效的步骤"}
