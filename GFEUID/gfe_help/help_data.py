"""Structured help data for the help command image card."""

from ..utils.image import GFE_ACCENT, GFE_BLUE

HELP_DATA = [
    {
        "name": "账号管理",
        "color": GFE_ACCENT,
        "items": [
            {"name": "登录 / 绑定", "desc": "浏览器页面登录，支持短信/密码/Token", "eg": "{prefix}登录"},
            {"name": "绑定状态", "desc": "查看当前绑定信息", "eg": "{prefix}绑定状态"},
            {"name": "删除绑定", "desc": "删除已绑定的GF2账号", "eg": "{prefix}删除绑定"},
        ],
    },
    {
        "name": "Wiki查询",
        "color": GFE_BLUE,
        "items": [
            {"name": "角色Wiki", "desc": "查询角色技能/命座/图鉴", "eg": "{prefix}黛烟 / {prefix}黛烟技能"},
            {"name": "武器Wiki", "desc": "查询武器详情", "eg": "{prefix}女武神武器"},
            {"name": "角色攻略", "desc": "查看角色攻略图片", "eg": "{prefix}黛烟攻略"},
            {"name": "角色列表", "desc": "查看全部角色列表", "eg": "{prefix}角色列表"},
            {"name": "武器列表", "desc": "查看五星武器列表", "eg": "{prefix}武器列表"},
            {"name": "刷新Wiki", "desc": "清除Wiki缓存 (Bot主人)", "eg": "{prefix}刷新wiki"},
        ],
    },
    {
        "name": "签到与社区",
        "color": (100, 200, 100),
        "items": [
            {"name": "签到", "desc": "手动签到领取每日奖励", "eg": "{prefix}签到"},
            {"name": "一键社区", "desc": "社区任务 + 兑换 + 签到", "eg": "{prefix}一键社区"},
            {"name": "开启/关闭自动社区", "desc": "每日自动社区开关", "eg": "{prefix}开启自动社区 / 关闭自动社区"},
            {"name": "开启/关闭自动兑换", "desc": "自动兑换开关", "eg": "{prefix}开启自动兑换 / 关闭自动兑换"},
            {"name": "兑换列表", "desc": "查看可兑换物品(标注个人/全局)", "eg": "{prefix}兑换列表"},
            {"name": "兑换设置", "desc": "设置个人兑换物品ID，不传ID则清除", "eg": "{prefix}兑换设置 1 3 5"},
            {"name": "自动任务状态", "desc": "查看自动社区/兑换及最后签到", "eg": "{prefix}自动任务状态"},
        ],
    },
    {
        "name": "Bot主人",
        "color": (210, 60, 50),
        "items": [
            {"name": "全部签到", "desc": "为所有已绑定用户签到", "eg": "{prefix}全部签到"},
            {"name": "全部一键社区", "desc": "为所有已绑定用户执行一键社区", "eg": "{prefix}全部一键社区"},
        ],
    },
]
