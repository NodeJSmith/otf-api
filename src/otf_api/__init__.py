from logging import basicConfig, getLogger

from .api import Otf
from .auth import OtfUser

basicConfig(level="INFO")
logger = getLogger(__name__)

__version__ = "0.8.3-dev2"


__all__ = ["Otf", "OtfUser"]
