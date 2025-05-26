from importlib.metadata import version
from logging import getLogger

from diskcache import Cache
from packaging.version import Version
from platformdirs import user_cache_dir

_CACHE = None
DEVICE_KEYS = ["device_key", "device_group_key", "device_password"]
TOKEN_KEYS = ["access_token", "id_token", "refresh_token"]

LOGGER = getLogger(__name__)


class OtfCache(Cache):
    """Small wrapper around diskcache.Cache to handle OTF API specific caching.

    This class provides methods to write and read device data and token data to/from the cache.
    It also provides methods to clear the cache and specific tags.
    """

    def write_device_data_to_cache(self, device_data: dict[str, str]) -> None:
        """Writes device data to the cache.

        Args:
            device_data (dict[str, str]): The device data to write to the cache.
        """
        try:
            if not any(device_data.values()):
                LOGGER.debug("No device data to write to cache")
                return

            for key, value in device_data.items():
                self.set(key, value, tag="device")
        except Exception:
            LOGGER.exception("Failed to write device key cache")

    def read_device_data_from_cache(self) -> dict[str, str | None]:
        """Reads device data from the cache.

        Returns:
            dict[str, str]: The device data read from the cache.
        """
        try:
            dd = {k: self.get(k) for k in DEVICE_KEYS}
            if not any(dd.values()):
                return {}
            return dd  # type: ignore
        except Exception:
            LOGGER.exception("Failed to read device key cache")
            return {}

    def write_token_data_to_cache(self, token_data: dict[str, str], expiration: int | None = None) -> None:
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
                self.set(key, value, tag="token", expire=expiration)
        except Exception:
            LOGGER.exception("Failed to write token cache")

    def read_token_data_from_cache(self) -> dict[str, str | None]:
        """Reads token data from the cache.

        Returns:
            dict[str, str | None]: The token data read from the cache.
        """
        try:
            tokens = {k: self.get(k) for k in TOKEN_KEYS}  # type: ignore
            if not any(tokens.values()):
                return {}
            return tokens  # type: ignore
        except Exception:
            LOGGER.exception("Failed to read token cache")
            return {}

    def clear_tokens(self) -> None:
        """Clears the token cache."""
        try:
            self.evict(tag="token", retry=True)
        except Exception:
            LOGGER.exception("Failed to clear token cache")

    def clear_device_data(self) -> None:
        """Clears the device data cache."""
        try:
            self.evict(tag="device", retry=True)
        except Exception:
            LOGGER.exception("Failed to clear device key cache")

    def clear(self) -> None:
        """Clears the cache."""
        try:
            self.clear()
        except Exception:
            LOGGER.exception("Failed to clear cache")


def get_cache_dir() -> str:
    """Returns the cache directory for the OTF API.

    The cache directory is based on the version of the OTF API package.

    Returns:
        str: The cache directory path.
    """
    otf_version = Version(version("otf-api"))
    otf_version_major = f"v{otf_version.major}"
    cache_dir = user_cache_dir("otf-api", version=otf_version_major)
    return cache_dir


def get_cache() -> OtfCache:
    """Returns the cache instance, creating it if it does not exist.

    Returns:
        Cache: The cache instance.
    """
    global _CACHE
    if _CACHE is None:
        cache_dir = get_cache_dir()
        LOGGER.debug("Using cache directory: %s", cache_dir)
        _CACHE = OtfCache(cache_dir)
    return _CACHE
