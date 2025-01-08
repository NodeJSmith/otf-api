import json
from logging import getLogger
from pathlib import Path

import attrs

LOGGER = getLogger(__name__)


@attrs.define
class CacheableData:
    """Represents a cacheable data object, with methods to read and write to cache."""

    name: str
    cache_dir: Path

    @property
    def cache_path(self) -> Path:
        """The path to the cache file."""
        return self.cache_dir.expanduser().joinpath(f"{self.name}_cache.json")

    def get_cached_data(self, keys: list[str] | None = None) -> dict[str, str]:
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
            if not keys:
                return data

            if set(data.keys()).issuperset(set(keys)):
                return {k: v for k, v in data.items() if k in keys}
            raise ValueError(f"Data must contain all keys: {keys}")
        except Exception:
            LOGGER.exception(f"Failed to read {self.cache_path.name}")
            return {}

    def write_to_cache(self, data: dict[str, str]) -> None:
        """Writes the data to the cache file."""
        LOGGER.debug(f"Writing {self.name} to cache ({self.cache_path})")

        existing_data = self.get_cached_data()
        data = {**existing_data, **data}

        self.cache_path.write_text(json.dumps(data, indent=4, default=str))

    def clear_cache(self, keys: list[str] | None = None) -> None:
        """Deletes the cache file if it exists."""
        if not self.cache_path.exists():
            return

        if not keys:
            self.cache_path.unlink()
            LOGGER.debug(f"{self.name} cache deleted")

        assert isinstance(keys, list), "Keys must be a list"

        data = self.get_cached_data()
        for key in keys:
            data.pop(key, None)

        self.write_to_cache(data)
