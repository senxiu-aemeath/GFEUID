import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from gsuid_core.data_store import get_res_path

MAIN_PATH = get_res_path() / "GFEuid"
sys.path.append(str(MAIN_PATH))

# 配置文件
CONFIG_PATH = MAIN_PATH / "config.json"
GUIDE_CONFIG_PATH = MAIN_PATH / "guide_config.json"

# 用户数据
PLAYER_PATH = MAIN_PATH / "players"

# 缓存
CACHE_PATH = MAIN_PATH / "cache"
WIKI_CACHE_PATH = MAIN_PATH / "wiki_cache"

# 攻略图片存储
GUIDE_PATH = MAIN_PATH / "guide"

# 其他素材
OTHER_PATH = MAIN_PATH / "other"
BAKE_PATH = OTHER_PATH / "bake"

# 别名文件
ALIAS_PATH = MAIN_PATH / "alias"
CHAR_ALIAS_PATH = ALIAS_PATH / "char_alias.json"
WEAPON_ALIAS_PATH = ALIAS_PATH / "weapon_alias.json"

# 自定义资源
CUSTOM_CARD_PATH = MAIN_PATH / "custom_role_pile"
CUSTOM_BG_PATH = MAIN_PATH / "custom_bg"

# 模板路径
TEMP_PATH = Path(__file__).parents[1] / "templates"
gfe_templates = Environment(
    loader=FileSystemLoader([str(TEMP_PATH)])
)


def init_dir():
    for d in [
        MAIN_PATH,
        PLAYER_PATH,
        CACHE_PATH,
        WIKI_CACHE_PATH,
        GUIDE_PATH,
        OTHER_PATH,
        BAKE_PATH,
        ALIAS_PATH,
        CUSTOM_CARD_PATH,
        CUSTOM_BG_PATH,
    ]:
        d.mkdir(parents=True, exist_ok=True)
