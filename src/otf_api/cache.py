from logging import getLogger
from pathlib import Path

from diskcache import Cache

LOGGER = getLogger(__name__)

CACHE = Cache(Path("~/.otf-api").expanduser())

DEVICE_KEYS = ["device_key", "device_group_key", "device_password"]
TOKEN_KEYS = ["access_token", "id_token", "refresh_token"]


def write_device_data_to_cache(device_data: dict[str, str]) -> None:
    """Writes device data to the cache.

    Args:
        device_data (dict[str, str]): The device data to write to the cache.
    """
    try:
        if not any(device_data.values()):
            LOGGER.debug("No device data to write to cache")
            return

        for key, value in device_data.items():
            CACHE.set(key, value)
    except Exception:
        LOGGER.exception("Failed to write device key cache")


def read_device_data_from_cache() -> dict[str, str | None]:
    """Reads device data from the cache.

    Returns:
        dict[str, str]: The device data read from the cache.
    """
    try:
        dd = {k: CACHE.get(k) for k in DEVICE_KEYS}
        if not any(dd.values()):
            return {}
        return dd  # type: ignore
    except Exception:
        LOGGER.exception("Failed to read device key cache")
        return {}


def write_token_data_to_cache(token_data: dict[str, str], expiration: int | None = None) -> None:
    """Writes token data to the cache.

    Args:
        token_data (dict[str, str]): The token data to write to the cache.
        expiration (int | None): The expiration time in seconds for the cache entry. Defaults to None.
    """
    try:
        if not any(token_data.values()):
            LOGGER.debug("No token data to write to cache")
            return

        for key, value in token_data.items():
            if expiration:
                CACHE.set(key, value, expire=expiration)
            else:
                CACHE.set(key, value)
    except Exception:
        LOGGER.exception("Failed to write token cache")


def read_token_data_from_cache() -> dict[str, str | None]:
    """Reads token data from the cache.

    Returns:
        dict[str, str | None]: The token data read from the cache.
    """
    try:
        tokens = {k: CACHE.get(k) for k in TOKEN_KEYS}  # type: ignore
        if not any(tokens.values()):
            return {}
        return tokens  # type: ignore
    except Exception:
        LOGGER.exception("Failed to read token cache")
        return {}


def clear() -> None:
    """Clears the cache."""
    try:
        CACHE.clear()
    except Exception:
        LOGGER.exception("Failed to clear cache")
