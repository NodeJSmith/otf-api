import os
import sys

from loguru import logger

from .api import Otf
from .auth import OtfUser

__version__ = "0.6.3"


__all__ = ["Otf", "OtfUser"]

logger.remove()
logger.add(sink=sys.stdout, level=os.getenv("OTF_LOG_LEVEL", "INFO"))
