import json
from logging import getLogger
from pathlib import Path

import attrs

LOGGER = getLogger(__name__)


@attrs.define
class CacheableData:
    """Represents a cacheable data object, with methods to read and write to cache."""

    name: str
    keys: list[str]
    cache_dir: Path

    @property
    def cache_path(self) -> Path:
        """The path to the cache file."""
        return self.cache_dir.joinpath(f"{self.name}_cache.json")

    def get_cached_data(self) -> dict[str, str]:
        """Reads the cache file and returns the data if it exists and is valid.

        Returns:
            dict[str, str]: The cached data, or an empty dictionary if the cache is invalid or missing.
        """
        LOGGER.debug(f"Loading {self.name} from cache ({self.cache_path})")
        try:
            if not self.cache_path.exists():
                return {}

            if self.cache_path.stat().st_size == 0:
                return {}

            data: dict[str, str] = json.loads(self.cache_path.read_text())
            if set(data.keys()).issuperset(set(self.keys)):
                return {k: v for k, v in data.items() if k in self.keys}

            return {}
        except Exception:
            LOGGER.exception(f"Failed to read {self.cache_path.name}")
            return {}

    def write_to_cache(self, data: dict[str, str]) -> None:
        """Writes the data to the cache file."""
        LOGGER.debug(f"Writing {self.name} to cache ({self.cache_path})")

        if not all(k in data for k in self.keys):
            raise ValueError(f"Data must contain all keys: {self.keys}")

        data = {k: v for k, v in data.items() if k in self.keys}

        try:
            self.cache_path.write_text(json.dumps(data, indent=4, default=str))
        except Exception:
            LOGGER.exception(f"Failed to write {self.cache_path.name}")

    def clear_cache(self) -> None:
        """Deletes the cache file if it exists."""
        if self.cache_path.exists():
            self.cache_path.unlink()
            LOGGER.debug(f"{self.name} cache deleted")
