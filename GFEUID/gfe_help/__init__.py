"""gfe_help - 帮助命令"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..gfe_config import PREFIX

sv_gfe_help = SV("GFE帮助", priority=1)


@sv_gfe_help.on_fullmatch(
    (f"{PREFIX}帮助", f"{PREFIX}help", f"{PREFIX}命令", f"{PREFIX}菜单"),
    block=True,
)
async def send_help(bot: Bot, ev: Event):
    await bot.send(
        f"━━━━ GFEuid · 少前2插件 ━━━━\n"
        f"\n"
        f"▸ {PREFIX}登录 / {PREFIX}绑定\n"
        f"  浏览器网页登录 GF2 账号\n"
        f"\n"
        f"▸ {PREFIX}绑定状态\n"
        f"  查看当前绑定信息\n"
        f"\n"
        f"▸ {PREFIX}删除绑定\n"
        f"  删除已绑定的 GF2 账号\n"
        f"\n"
        f"▸ {PREFIX}<角色名>\n"
        f"  查询角色 Wiki（支持 技能/命座/wiki/介绍/图鉴 后缀）\n"
        f"  例：{PREFIX}黛烟 / {PREFIX}黛烟技能 / {PREFIX}黛烟命座\n"
        f"\n"
        f"▸ {PREFIX}<武器名>武器\n"
        f"  查询武器 Wiki\n"
        f"  例：{PREFIX}女武神武器\n"
        f"\n"
        f"▸ {PREFIX}<角色名>攻略\n"
        f"  查看角色攻略图片\n"
        f"  例：{PREFIX}黛烟攻略\n"
        f"\n"
        f"▸ {PREFIX}角色列表\n"
        f"  查看全部角色列表\n"
        f"\n"
        f"▸ {PREFIX}武器列表\n"
        f"  查看五星武器列表\n"
        f"\n"
        f"▸ {PREFIX}刷新wiki (Bot主人)\n"
        f"  清除 Wiki 缓存\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
