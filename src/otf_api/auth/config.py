import os
from pathlib import Path
from typing import ClassVar

import attrs

from otf_api.utils import CacheableData


@attrs.define
class OtfAuthConfig:
    DEVICE_DATA_KEYS: ClassVar[list[str]] = ["device_key", "device_group_key", "device_password"]
    TOKEN_KEYS: ClassVar[list[str]] = ["access_token", "id_token", "refresh_token"]

    cache_device_data: bool = True
    cache_tokens_plaintext: bool = False

    cache_path: Path = attrs.field(init=False)
    dd_cache: CacheableData = attrs.field(init=False)
    token_cache: CacheableData = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        self.cache_path = self._get_cache_path()
        self.dd_cache = CacheableData("device_key", self.DEVICE_DATA_KEYS, self.cache_path)
        self.token_cache = CacheableData("tokens", self.TOKEN_KEYS, self.cache_path)

    def _get_cache_path(self) -> Path:
        if "OTF_API_CACHE_PATH" in os.environ:
            cache_path = Path(os.environ["OTF_API_CACHE_PATH"])
        else:
            cache_path = Path("~/.otf-api")

        cache_path = cache_path.expanduser()
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
