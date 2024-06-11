import asyncio
import typing
from typing import Any

import aiohttp
from loguru import logger
from yarl import URL

from otf.classes_api import ClassesApi
from otf.dna_api import DnaApi
from otf.member_api import MemberApi
from otf.models.auth import User
from otf.studio_api import StudiosApi

if typing.TYPE_CHECKING:
    from loguru._logger import Logger

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_DNA_BASE_URL = "api.yuzu.orangetheory.com"
REQUEST_HEADERS = {"Authorization": None, "Content-Type": "application/json", "Accept": "application/json"}


class Api:
    logger: "Logger" = logger
    user: User
    session: aiohttp.ClientSession

    def __init__(self, username: str | None = None, password: str | None = None):
        self.user = User.load_from_disk(username, password)

        self.session = aiohttp.ClientSession()

        self.member_api = MemberApi(self)
        self.classes_api = ClassesApi(self)
        self.studios_api = StudiosApi(self)
        self.dna_api = DnaApi(self)

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(self._close_session())  # noqa
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._close_session())

    async def _close_session(self):
        if not self.session.closed:
            await self.session.close()

    @property
    def base_headers(self):
        """Get the base headers for the API."""
        if not self.user:
            raise ValueError("No user is logged in.")

        return {
            "Authorization": f"Bearer {self.user.cognito.id_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _do(self, method: str, base_url: str, url: str, params: dict[str, Any] | None = None, **kwargs) -> dict:
        """Perform an API request."""

        params = params or {}
        params = {k: v for k, v in params.items() if v is not None}

        full_url = str(URL.build(scheme="https", host=base_url, path=url))

        logger.debug(f"Making {method!r} request to {full_url}")

        if "headers" in kwargs:
            headers = kwargs.pop("headers")
            headers.update(self.base_headers)
        else:
            headers = self.base_headers

        async with self.session.request(method, full_url, headers=headers, params=params, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    async def _classes_request(self, method: str, url: str, params: dict[str, Any] | None = None, **kwargs) -> dict:
        """Perform an API request to the classes API."""
        return await self._do(method, API_IO_BASE_URL, url, params, **kwargs)

    async def _default_request(self, method: str, url: str, params: dict[str, Any] | None = None, **kwargs) -> dict:
        """Perform an API request to the default API."""
        return await self._do(method, API_BASE_URL, url, params, **kwargs)

    async def _dna_request(self, method: str, url: str, params: dict[str, Any] | None = None, **kwargs) -> dict:
        """Perform an API request to the DNA API."""
        return await self._do(method, API_DNA_BASE_URL, url, params, **kwargs)
