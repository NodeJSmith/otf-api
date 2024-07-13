import os
import sys

from loguru import logger

from .api import Otf
from .auth import User

__version__ = "0.3.0"


__all__ = ["Otf", "User"]

logger.remove()
logger.add(sink=sys.stdout, level=os.getenv("OTF_LOG_LEVEL", "INFO"))
