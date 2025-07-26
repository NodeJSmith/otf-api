"""Unofficial Orangetheory API client.

This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness.
Use it at your own risk. It may break at any time if Orangetheory changes their services.
"""

import logging
import os

import coloredlogs

from otf_api import models
from otf_api.api import Otf
from otf_api.auth import OtfUser

LOG_LEVEL = os.getenv("OTF_LOG_LEVEL", "INFO").upper()

LOG_FMT = "%(asctime)s - %(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"


def _setup_logging() -> None:
    logger = logging.getLogger("otf_api")

    if logger.handlers:
        return  # Already set up

    # 2) Set the logger level to INFO (or whatever you need).
    logger.setLevel(LOG_LEVEL)

    # 3) Create a handler (e.g., console) and set its formatter.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=DATE_FMT, style="%"))

    # 4) Add this handler to your package logger.
    logger.addHandler(handler)

    coloredlogs.install(
        level=LOG_LEVEL,
        logger=logger,
        fmt=LOG_FMT,
        datefmt=DATE_FMT,
        style="%",
        isatty=True,  # Use colored output only if the output is a terminal
    )


_setup_logging()

__version__ = "0.15.2"


__all__ = ["Otf", "OtfUser", "models"]
