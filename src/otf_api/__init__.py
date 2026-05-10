"""Unofficial Orangetheory API client.

This software is not affiliated with, endorsed by, or supported by Orangetheory Fitness.
Use it at your own risk. It may break at any time if Orangetheory changes their services.
"""

import logging
import os

import coloredlogs

from otf_api import exceptions, models
from otf_api.anonymize.anonymizer import AnonymizeConfig, Anonymizer
from otf_api.api import Otf
from otf_api.auth import OtfUser

LOG_LEVEL = os.getenv("OTF_LOG_LEVEL", "INFO").upper()

LOG_FMT = "%(asctime)s - %(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"


def _setup_logging() -> None:
    logger = logging.getLogger("otf_api")

    if logger.handlers:
        return

    logger.setLevel(LOG_LEVEL)

    coloredlogs.install(
        level=LOG_LEVEL,
        logger=logger,
        fmt=LOG_FMT,
        datefmt=DATE_FMT,
        style="%",
    )


_setup_logging()

__all__ = ["AnonymizeConfig", "Anonymizer", "Otf", "OtfUser", "exceptions", "models"]
