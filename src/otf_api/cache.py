import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
from collections.abc import Callable
from functools import wraps
from importlib.metadata import version
from logging import getLogger
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from packaging.version import Version
from platformdirs import user_cache_dir

_CACHE = None
DEVICE_KEYS = ["device_key", "device_group_key", "device_password"]
TOKEN_KEYS = ["access_token", "id_token", "refresh_token"]

LOGGER = getLogger(__name__)
_CACHE_DIR_MODE = 0o700
TOKEN_FILE = "tokens.json"
DEVICE_FILE = "device.json"
RESPONSES_DIR = "responses"
# Files left behind by the diskcache-backed cache that older versions used.
LEGACY_DISKCACHE_FILES = ["cache.db", "cache.db-wal", "cache.db-shm"]

P = ParamSpec("P")
R = TypeVar("R")


class OtfCache:
    """File-backed cache for OTF credentials and memoized API responses.

    Everything is stored as JSON in owner-only files, so reading the cache never executes code. Tokens and
    device data live in their own files; memoized responses live under ``responses/<tag>/``.
    """

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    @property
    def token_path(self) -> Path:
        """Path of the cached Cognito tokens."""
        return self.directory / TOKEN_FILE

    @property
    def device_path(self) -> Path:
        """Path of the cached device registration."""
        return self.directory / DEVICE_FILE

    @property
    def responses_dir(self) -> Path:
        """Directory holding memoized responses, one subdirectory per tag."""
        return self.directory / RESPONSES_DIR

    def write_device_data_to_cache(self, device_data: dict[str, str]) -> None:
        """Merges device data into the cache.

        Args:
            device_data (dict[str, str]): The device data to write to the cache.
        """
        try:
            if not any(device_data.values()):
                LOGGER.debug("No device data to write to cache")
                return

            existing = read_json(self.device_path) or {}
            write_json(self.device_path, {**existing, **device_data})
        except Exception:
            LOGGER.exception("Failed to write device key cache")

    def read_device_data_from_cache(self) -> dict[str, str | None]:
        """Reads device data from the cache.

        Returns:
            dict[str, str | None]: The device data read from the cache, or an empty dict if there is none.
        """
        try:
            stored = read_json(self.device_path) or {}
            dd = {k: stored.get(k) for k in DEVICE_KEYS}
            if not any(dd.values()):
                return {}
            return dd
        except Exception:
            LOGGER.exception("Failed to read device key cache")
            return {}

    def write_token_data_to_cache(self, token_data: dict[str, str], expiration: int | None = None) -> None:
        """Merges token data into the cache.

        Args:
            token_data (dict[str, str]): The token data to write to the cache.
            expiration (int | None): Seconds until all cached tokens expire. Defaults to None (no expiry).
        """
        try:
            if not any(token_data.values()):
                LOGGER.debug("No token data to write to cache")
                return

            existing = read_unexpired(self.token_path) or {}
            write_entry(self.token_path, {**existing, **token_data}, expiration)
        except Exception:
            LOGGER.exception("Failed to write token cache")

    def read_token_data_from_cache(self) -> dict[str, str | None]:
        """Reads token data from the cache.

        Returns:
            dict[str, str | None]: The token data read from the cache, or an empty dict if there is none.
        """
        try:
            stored = read_unexpired(self.token_path) or {}
            tokens = {k: stored.get(k) for k in TOKEN_KEYS}
            if not any(tokens.values()):
                return {}
            return tokens
        except Exception:
            LOGGER.exception("Failed to read token cache")
            return {}

    def clear_tokens(self) -> None:
        """Clears the token cache."""
        try:
            self.token_path.unlink(missing_ok=True)
        except Exception:
            LOGGER.exception("Failed to clear token cache")

    def clear_device_data(self) -> None:
        """Clears the device data cache."""
        try:
            self.device_path.unlink(missing_ok=True)
        except Exception:
            LOGGER.exception("Failed to clear device key cache")

    def evict(self, tag: str) -> None:
        """Removes every memoized response stored under a tag.

        Args:
            tag (str): The tag passed to `memoize`.
        """
        shutil.rmtree(self.responses_dir / tag, ignore_errors=True)

    def purge_expired_responses(self) -> None:
        """Deletes expired memoized responses, which are otherwise only removed when the same call is repeated."""
        for path in self.responses_dir.glob("*/*.json"):
            try:
                read_unexpired(path)
            except OSError:
                LOGGER.warning("Could not purge cached response %s", path, exc_info=True)

    def clear(self) -> None:
        """Clears tokens, device data, and memoized responses."""
        self.clear_tokens()
        self.clear_device_data()
        shutil.rmtree(self.responses_dir, ignore_errors=True)

    def memoize(self, expire: int, tag: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Memoize a client method's JSON result on disk, keyed by the client's member UUID and the arguments.

        Args:
            expire (int): Seconds until a cached result expires.
            tag (str): Groups the results so `evict` can remove them.

        Returns:
            Callable: The decorator.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                client, *rest = args
                key = json.dumps(
                    [func.__qualname__, getattr(client, "member_uuid", None), rest, kwargs],
                    sort_keys=True,
                    default=str,
                )
                path = self.responses_dir / tag / f"{hashlib.sha256(key.encode()).hexdigest()}.json"

                try:
                    cached = read_unexpired(path)
                except Exception:
                    LOGGER.exception("Failed to read cached response", extra={"tag": tag})
                    cached = None
                if cached is not None and "value" in cached:
                    return cached["value"]

                result = func(*args, **kwargs)
                try:
                    write_entry(path, {"value": result}, expire)
                except Exception:
                    LOGGER.exception("Failed to cache response", extra={"tag": tag})
                return result

            return wrapper

        return decorator


def read_json(path: Path) -> dict[str, Any] | None:
    """Reads a JSON object from a file, returning None when the file is missing or unreadable as an object."""
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError):
        LOGGER.warning("Ignoring corrupt cache file", extra={"path": str(path)})
        path.unlink(missing_ok=True)
        return None
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Atomically writes a JSON object to a file only the owner can read."""
    path.parent.mkdir(mode=_CACHE_DIR_MODE, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")  # mkstemp creates it 0600
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_entry(path: Path, data: dict[str, Any], expire: int | None) -> None:
    """Writes `data` with an optional expiry, `expire` seconds from now."""
    expires_at = time.time() + expire if expire is not None else None
    write_json(path, {**data, "_expires_at": expires_at})


def read_unexpired(path: Path) -> dict[str, Any] | None:
    """Reads an entry written by `write_entry`, deleting and ignoring it once it has expired."""
    data = read_json(path)
    if data is None:
        return None
    expires_at = data.pop("_expires_at", None)
    if expires_at is not None and expires_at <= time.time():
        path.unlink(missing_ok=True)
        return None
    return data


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


def ensure_secure_directory(path: str) -> None:
    """Create the cache directory with restrictive permissions (owner-only access).

    Tightens an existing directory to mode 0700 if it is looser. If the permissions
    cannot be changed (e.g. the directory is owned by another user or on a read-only
    filesystem), logs a warning and continues rather than making the library unusable.

    Args:
        path: The directory path to create and secure.
    """
    path_obj = Path(path)
    path_obj.mkdir(mode=_CACHE_DIR_MODE, parents=True, exist_ok=True)
    if stat.S_IMODE(path_obj.stat().st_mode) == _CACHE_DIR_MODE:
        return

    try:
        path_obj.chmod(_CACHE_DIR_MODE)
    except OSError:
        LOGGER.warning("Could not set restrictive permissions on cache directory: %s", path, exc_info=True)


def remove_legacy_diskcache(path: str) -> None:
    """Deletes the diskcache database and value directories older versions left in the cache directory.

    Their tokens are never read again, so users sign in once more after upgrading.

    Args:
        path: The cache directory.
    """
    cache_dir = Path(path)
    if not (cache_dir / "cache.db").exists():
        return

    LOGGER.info("Removing legacy diskcache files from %s", path)
    try:
        for name in LEGACY_DISKCACHE_FILES:
            (cache_dir / name).unlink(missing_ok=True)
        # diskcache spills large values into two-level hex directories (e.g. "3f/a1/<hash>.val").
        for child in cache_dir.iterdir():
            if child.is_dir() and len(child.name) == 2 and all(c in "0123456789abcdef" for c in child.name):
                shutil.rmtree(child, ignore_errors=True)
    except OSError:
        LOGGER.warning("Could not remove legacy diskcache files from %s", path, exc_info=True)


def get_cache() -> OtfCache:
    """Returns the cache instance, creating it if it does not exist.

    Creates the cache directory with owner-only permissions (0700) to prevent
    other local users from reading cached authentication tokens.

    Returns:
        OtfCache: The cache instance.
    """
    global _CACHE
    if _CACHE is None:
        cache_dir = get_cache_dir()
        ensure_secure_directory(cache_dir)
        remove_legacy_diskcache(cache_dir)
        LOGGER.debug("Using cache directory: %s", cache_dir)
        _CACHE = OtfCache(cache_dir)
        _CACHE.purge_expired_responses()
    return _CACHE


def clear_cache() -> None:
    """Clears tokens, device data, and memoized responses."""
    try:
        get_cache().clear()
    except Exception:
        LOGGER.exception("Failed to clear cache")
