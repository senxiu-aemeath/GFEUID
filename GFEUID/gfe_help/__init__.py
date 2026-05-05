"""gfe_help - 帮助命令"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..gfe_config import PREFIX

sv_gfe_help = SV("GFE帮助", priority=1)


@sv_gfe_help.on_fullmatch(
    ("帮助", "help", "命令", "菜单"),
    block=True,
)
async def send_help(bot: Bot, ev: Event):
    await bot.send(
        f"━━━━ GFEuid · 少前2插件 ━━━━\n"
        f"\n"
        f"▸ {PREFIX}登录 / {PREFIX}绑定\n"
        f"  浏览器页面登录，支持验证码/密码/Token 三种方式\n"
        f"  已绑定用户再次打开可升级绑定或切换账号\n"
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
        f"▸ {PREFIX}签到\n"
        f"  手动签到\n"
        f"\n"
        f"▸ {PREFIX}一键社区\n"
        f"  手动执行社区任务+兑换+签到\n"
        f"\n"
        f"▸ {PREFIX}开启自动社区 / {PREFIX}关闭自动社区\n"
        f"  开关每日自动一键社区\n"
        f"\n"
        f"▸ {PREFIX}开启自动兑换 / {PREFIX}关闭自动兑换\n"
        f"  开关自动兑换\n"
        f"\n"
        f"▸ {PREFIX}兑换列表\n"
        f"  查看可兑换物品（标注个人/全局设置）\n"
        f"\n"
        f"▸ {PREFIX}兑换设置 <物品ID...>\n"
        f"  设置个人兑换物品，不传ID则清除回退全局\n"
        f"\n"
        f"▸ {PREFIX}自动任务状态\n"
        f"  查看自动社区/兑换设置及最后签到时间\n"
        f"\n"
        f"▸ {PREFIX}全部签到 (Bot主人)\n"
        f"  为所有已绑定用户签到\n"
        f"\n"
        f"▸ {PREFIX}全部一键社区 (Bot主人)\n"
        f"  为所有已绑定用户执行一键社区\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
