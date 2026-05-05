from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .gfe_config import GfeConfig

sv_gfe_config = SV("GFE配置", priority=3)

PREFIX = get_plugin_available_prefix("GFEUID")
