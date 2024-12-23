import logging
from logging import basicConfig

from .api import Otf
from .auth import OtfUser
from .sync_api import OtfSync

LOG_FMT = "{asctime} - {module}.{funcName}:{lineno} - {levelname} - {message}"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"

basicConfig(level="INFO", style="{", format=LOG_FMT, datefmt=DATE_FMT)
logging.getLogger("httpx").setLevel(logging.WARNING)

__version__ = "0.9.2"


__all__ = ["Otf", "OtfSync", "OtfUser"]
