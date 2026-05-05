from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
    GsListStrConfig,
)

CONFIG_DEFAULT: Dict[str, GSC] = {
    "GfeLoginUrl": GsStrConfig(
        "GF2登录url",
        "用于设置GFEuid登录界面的域名，留空则自动使用服务器地址",
        "",
    ),
    "GfeLoginUrlSelf": GsBoolConfig(
        "强制【GF2登录url】为自己的域名",
        "外置登录服务请关闭；自己穿透或VPS反代请打开",
        False,
    ),
    "GfeQRLogin": GsBoolConfig(
        "开启后，登录链接变成二维码",
        "开启后，登录链接变成二维码",
        False,
    ),
    "GfeLoginForward": GsBoolConfig(
        "开启后，登录链接变为转发消息",
        "开启后，登录链接变为转发消息",
        False,
    ),
    "GfeGuide": GsListStrConfig(
        "角色攻略图提供方",
        "使用gfe角色攻略时选择的提供方",
        ["all"],
        options=["all"],
    ),
    "GfeGuideMaxSize": GsIntConfig(
        "攻略图片最大大小(M)",
        "发送攻略图片前会自动转为jpg格式，若超过此大小则自动压缩，单位MB",
        5,
        50,
    ),
    "WikiCacheTtlDays": GsIntConfig(
        "Wiki数据缓存天数",
        "Wiki角色/武器列表数据的缓存有效期",
        3,
        30,
    ),
    "WikiRenderCacheTtlDays": GsIntConfig(
        "Wiki渲染图缓存天数",
        "Wiki渲染图片的缓存有效期",
        7,
        60,
    ),
    "ScreenshotWidth": GsIntConfig(
        "Wiki截图宽度",
        "Playwright渲染Wiki时的视口宽度",
        800,
        1920,
    ),
}
