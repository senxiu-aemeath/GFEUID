"""gfeuid - Girls' Frontline 2: Exilium UID Plugin"""

from pathlib import Path

from gsuid_core.sv import SL, Plugins
from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path

if "gfeuid" not in SL.plugins:
    Plugins(name="gfeuid", force_prefix=["gfe"], allow_empty_prefix=False)

from .utils.resource.RESOURCE_PATH import init_dir, MAIN_PATH

init_dir()

# 清理旧登录缓存
_old_cache = MAIN_PATH / "login_cache.db"
if _old_cache.exists():
    try:
        _old_cache.unlink()
        logger.info("[GFEuid] 已删除旧的 login_cache.db")
    except Exception:
        pass

logger.info("[GFEuid] 插件初始化完成")
