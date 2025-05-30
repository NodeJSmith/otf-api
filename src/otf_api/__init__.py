"""Unofficial Orangetheory API client.

This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness.
Use it at your own risk. It may break at any time if Orangetheory changes their services.
"""

import logging
import os

from otf_api import models
from otf_api.api import Otf
from otf_api.auth import OtfUser

LOG_LEVEL = os.getenv("OTF_LOG_LEVEL", "INFO").upper()
LOG_LEVEL_NUM = getattr(logging, LOG_LEVEL, logging.INFO)
LOG_FMT = "{asctime} - {module}.{funcName}:{lineno} - {levelname} - {message}"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"


def _setup_logging() -> None:
    logger = logging.getLogger("otf_api")

    if logger.handlers:
        return  # Already set up

    # 2) Set the logger level to INFO (or whatever you need).
    logger.setLevel(LOG_LEVEL_NUM)

    # 3) Create a handler (e.g., console) and set its formatter.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=DATE_FMT, style="{"))

    # 4) Add this handler to your package logger.
    logger.addHandler(handler)


_setup_logging()

__version__ = "0.13.3"


__all__ = ["Otf", "OtfUser", "models"]
