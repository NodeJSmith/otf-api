from logging import basicConfig

from .api import Otf
from .auth import OtfUser

LOG_FMT = "{asctime} - {module}.{funcName}:{lineno} - {levelname} - {message}"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"

basicConfig(level="INFO", style="{", format=LOG_FMT, datefmt=DATE_FMT)

__version__ = "0.8.3-dev3"


__all__ = ["Otf", "OtfUser"]
