import os
import sys

from loguru import logger

from . import classes_api, member_api, studios_api, telemetry_api
from .api import Api
from .models.auth import User

__version__ = "0.2.2"


__all__ = ["Api", "User", "member_api", "studios_api", "classes_api", "telemetry_api"]

logger.remove()
logger.add(sink=sys.stdout, level=os.getenv("OTF_LOG_LEVEL", "INFO"))
