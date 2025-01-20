import logging
import os

LOG_LEVEL = os.getenv("OTF_LOG_LEVEL", "INFO")

LOG_FMT = "{asctime} - {module}.{funcName}:{lineno} - {levelname} - {message}"
DATE_FMT = "%Y-%m-%d %H:%M:%S%z"

logger = logging.getLogger("otf_api")

# 2) Set the logger level to INFO (or whatever you need).
logger.setLevel(LOG_LEVEL)

# 3) Create a handler (e.g., console) and set its formatter.
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=DATE_FMT, style="{"))

# 4) Add this handler to your package logger.
logger.addHandler(handler)
