import os
import sys

from loguru import logger

from .api import Api
from .models.auth import User

__version__ = "0.3.0"


__all__ = ["Api", "User"]

logger.remove()
logger.add(sink=sys.stdout, level=os.getenv("OTF_LOG_LEVEL", "INFO"))
