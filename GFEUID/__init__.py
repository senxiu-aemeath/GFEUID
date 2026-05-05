"""gfeuid - Girls' Frontline 2: Exilium UID Plugin"""

from pathlib import Path

from gsuid_core.sv import SL, Plugins
from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path

if "GFEUID" not in SL.plugins:
    Plugins(name="GFEUID", force_prefix=["gfe"], allow_empty_prefix=False)

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

# 显式导入子模块，确保 SV 注册
logger.info("[GFEuid] 开始导入子模块...")
try:
    from .gfe_config import sv_gfe_config  # noqa: F401
    logger.info("[GFEuid] gfe_config 导入成功")
except Exception as e:
    logger.error(f"[GFEuid] gfe_config 导入失败: {e}")

try:
    from .gfe_login import sv_gfe_login  # noqa: F401
    logger.info("[GFEuid] gfe_login 导入成功")
except Exception as e:
    logger.error(f"[GFEuid] gfe_login 导入失败: {e}")

try:
    from .gfe_wiki import sv_gfe_wiki  # noqa: F401
    logger.info("[GFEuid] gfe_wiki 导入成功")
except Exception as e:
    logger.error(f"[GFEuid] gfe_wiki 导入失败: {e}")

try:
    from .gfe_help import sv_gfe_help  # noqa: F401
    logger.info("[GFEuid] gfe_help 导入成功")
except Exception as e:
    logger.error(f"[GFEuid] gfe_help 导入失败: {e}")

from .version import __version__

logger.info(f"[GFEuid] 插件初始化完成 v{__version__}")
