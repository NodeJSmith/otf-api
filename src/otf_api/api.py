import asyncio
import typing
from typing import Any

import aiohttp
from loguru import logger
from yarl import URL

from otf_api.classes_api import ClassesApi
from otf_api.member_api import MemberApi
from otf_api.models.auth import User
from otf_api.performance_api import PerformanceApi
from otf_api.studios_api import StudiosApi
from otf_api.telemetry_api import TelemtryApi

if typing.TYPE_CHECKING:
    from loguru import Logger

    from otf_api.models.responses.member_detail import MemberDetail
    from otf_api.models.responses.studio_detail import StudioDetail

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
REQUEST_HEADERS = {"Authorization": None, "Content-Type": "application/json", "Accept": "application/json"}


class Api:
    """The main class of the otf-api library. Create an instance using the async method `create`.

    Example:
        ---
        ```python
        import asyncio
        from otf_api import Api

        async def main():
            otf = await Api.create("username", "password")
            print(otf.member)

        if __name__ == "__main__":
            asyncio.run(main())
        ```
    """

    logger: "Logger" = logger
    user: User
    session: aiohttp.ClientSession

    def __init__(self, username: str, password: str):
        self.member: MemberDetail
        self.home_studio: StudioDetail

        self.user = User.load_from_disk(username, password)
        self.session = aiohttp.ClientSession()

        self.member_api = MemberApi(self)
        self.classes_api = ClassesApi(self)
        self.studios_api = StudiosApi(self)
        self.telemetry_api = TelemtryApi(self)
        self.performance_api = PerformanceApi(self)

    @classmethod
    async def create(cls, username: str, password: str) -> "Api":
        """Create a new API instance. The username and password are required arguments because even though
        we cache the token, they expire so quickly that we usually end up needing to re-authenticate.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.
        """
        self = cls(username, password)
        self.member = await self.member_api.get_member_detail()
        self.home_studio = await self.studios_api.get_studio_detail(self.member.home_studio.studio_uuid)
        return self

    def __del__(self) -> None:
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(self._close_session())  # noqa
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._close_session())

    async def _close_session(self) -> None:
        if not self.session.closed:
            await self.session.close()

    @property
    def _base_headers(self) -> dict[str, str]:
        """Get the base headers for the API."""
        if not self.user:
            raise ValueError("No user is logged in.")

        return {
            "Authorization": f"Bearer {self.user.cognito.id_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _do(
        self,
        method: str,
        base_url: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Perform an API request."""

        params = params or {}
        params = {k: v for k, v in params.items() if v is not None}

        full_url = str(URL.build(scheme="https", host=base_url, path=url))

        logger.debug(f"Making {method!r} request to {full_url}, params: {params}")

        if headers:
            headers.update(self._base_headers)
        else:
            headers = self._base_headers

        async with self.session.request(method, full_url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def _classes_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the classes API."""
        return await self._do(method, API_IO_BASE_URL, url, params)

    async def _default_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the default API."""
        return await self._do(method, API_BASE_URL, url, params)

    async def _telemetry_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the Telemetry API."""
        return await self._do(method, API_TELEMETRY_BASE_URL, url, params)

    async def _performance_summary_request(
        self, method: str, url: str, headers: dict[str, str], params: dict[str, Any] | None = None
    ) -> Any:
        """Perform an API request to the performance summary API."""
        return await self._do(method, API_IO_BASE_URL, url, params, headers)
