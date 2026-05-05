"""gfe_login - 网页登录模块 + 绑定状态/删除绑定"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .login import page_login
from ..gfe_config import PREFIX
from ..utils.database.models import GfeBind, GfeUser

sv_gfe_login = SV("GFE登录")


@sv_gfe_login.on_command(
    ("登录", "登陆", "登入", "login", "dl", "绑定"),
    block=True,
)
async def handle_login(bot: Bot, ev: Event):
    return await page_login(bot, ev)


@sv_gfe_login.on_fullmatch(
    ("绑定状态", "绑定信息"),
    block=True,
)
async def bind_status(bot: Bot, ev: Event):
    user = await GfeUser.select_by_user(ev.user_id, ev.bot_id)
    if not user or not user.web_token:
        await bot.send(
            f"[GF2] 未绑定 GF2 账号\n请发送【{PREFIX}登录】",
            at_sender=True if ev.group_id else False,
        )
        return

    import time
    bind_time = (
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.last_bind_time))
        if user.last_bind_time else "未知"
    )
    server_name = "国服" if user.server == "cn" else "国际服"
    type_name = "短信验证码" if user.login_type == "sms" else "账号密码"

    await bot.send(
        f"[GF2] 绑定状态\n"
        f"昵称：{user.nickname or '未知'}\n"
        f"UID：{user.uid or '未知'}\n"
        f"服务器：{server_name}\n"
        f"登录方式：{type_name}\n"
        f"绑定时间：{bind_time}",
        at_sender=True if ev.group_id else False,
    )


@sv_gfe_login.on_fullmatch(
    ("删除绑定", "解绑", "删除token"),
    block=True,
)
async def delete_bind(bot: Bot, ev: Event):
    user = await GfeUser.select_by_user(ev.user_id, ev.bot_id)
    if not user or not user.web_token:
        await bot.send(
            f"[GF2] 未绑定 GF2 账号",
            at_sender=True if ev.group_id else False,
        )
        return

    await GfeUser.delete_user(ev.user_id, ev.bot_id)
    await bot.send(
        f"[GF2] 已删除 GF2 绑定信息\n" +
        (f"昵称：{user.nickname}  UID：{user.uid}" if user.nickname else ""),
        at_sender=True if ev.group_id else False,
    )
