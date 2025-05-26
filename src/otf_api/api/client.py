import atexit
import re
from json import JSONDecodeError
from logging import getLogger
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yarl import URL

from otf_api import exceptions as exc
from otf_api.api.utils import get_json_from_response, is_error_response
from otf_api.auth import OtfUser
from otf_api.cache import get_cache

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json",
    "user-agent": "okhttp/4.12.0",
}
CACHE = get_cache()
LOGGER = getLogger(__name__)


class OtfClient:
    """Client for interacting with the OTF API - generally to be used by the Otf class.

    This class provides methods to perform various API requests, including booking classes,
    retrieving member details, and managing bookings. It handles authentication and session management
    using the provided OtfUser instance or a default unauthenticated user.

    It also includes retry logic for handling transient errors and caching for performance optimization.
    """

    def __init__(self, user: OtfUser | None = None):
        """Initialize the OTF API client.

        Args:
            user (OtfUser): The user to authenticate as.
        """
        self.user = user or OtfUser()
        self.member_uuid = self.user.member_uuid

        self.session = httpx.Client(
            headers=HEADERS, auth=self.user.httpx_auth, timeout=httpx.Timeout(20.0, connect=60.0)
        )
        atexit.register(self.session.close)

    def _build_request(
        self,
        method: str,
        full_url: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
        **kwargs,
    ) -> httpx.Request:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        headers = headers or {}
        return self.session.build_request(method, full_url, headers=headers, params=params, **kwargs)

    @retry(
        retry=retry_if_exception_type((exc.RetryableOtfRequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def do(
        self,
        method: str,
        base_url: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> Any:  # noqa: ANN401
        """Perform an API request.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            base_url (str): The base URL for the API.
            path (str): The specific endpoint to request.
            params (dict[str, Any] | None): Query parameters to include in the request.
            headers (dict[str, str] | None): Additional headers to include in the request.
            **kwargs: Additional keyword arguments to pass to the request.

        Returns:
            Any: The response data from the API request.

        Raises:
            OtfRequestError: If the request fails or the response is invalid.
            HTTPStatusError: If the response status code indicates an error.
        """
        full_url = str(URL.build(scheme="https", host=base_url, path=path))
        request = self._build_request(method, full_url, params, headers, **kwargs)
        LOGGER.debug(f"Making {method!r} request to '{full_url}', params: {params}, headers: {headers}")

        try:
            response = self.session.send(request)
            response.raise_for_status()
        except Exception as e:
            self._handle_transport_error(e, request)
            raise

        return self._handle_response(method, response, request)

    def default_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the default API."""
        return self.do(method, API_BASE_URL, path, params, headers=headers, **kwargs)

    def _map_http_error(
        self, data: dict, error: httpx.HTTPStatusError, response: httpx.Response, request: httpx.Request
    ) -> None:
        code = data.get("code")
        path = request.url.path
        error_code = data.get("data", {}).get("errorCode")
        error_msg = data.get("message") or data.get("data", {}).get("message", "") or ""

        if response.status_code == 404:
            raise exc.ResourceNotFoundError(f"Resource not found: {path}")

        # Match based on error code and path
        if re.match(r"^/v1/bookings/me", path):
            if code == "BOOKING_CANCELED":
                raise exc.BookingAlreadyCancelledError(error_msg or "Booking was already cancelled")
            if code == "BOOKING_ALREADY_BOOKED":
                raise exc.AlreadyBookedError("This class is already booked")

        if re.match(r"^/member/members/.*?/bookings", path):
            if code == "NOT_AUTHORIZED" and error_msg.startswith("This class booking has been cancelled"):
                raise exc.BookingNotFoundError("Booking was already cancelled")
            if error_code == "603":
                raise exc.AlreadyBookedError("Class is already booked")
            if error_code == "602":
                raise exc.OutsideSchedulingWindowError("Class is outside scheduling window")

        msg = f"HTTP error {error.response.status_code} for {request.method} {request.url}"
        LOGGER.error(msg)
        error_cls = exc.RetryableOtfRequestError if response.status_code >= 500 else exc.OtfRequestError
        raise error_cls(message=msg, original_exception=error, request=request, response=response)

    def _handle_transport_error(self, error: Exception, request: httpx.Request) -> None:
        """Handle transport errors during API requests.

        Generally we let these bubble up to the caller so they get retried, but there are a few
        cases where we want to log the error and raise a specific exception.

        Args:
            error (Exception): The exception raised during the request.
            request (httpx.Request): The request that caused the error.
        """
        method = request.method
        url = request.url

        if not isinstance(error, httpx.HTTPStatusError):
            LOGGER.exception(f"Unexpected error during {method!r} {url!r}: {type(error).__name__} - {error}")
            return

        json_data = get_json_from_response(error.response)
        self._map_http_error(json_data, error, error.response, request)

        return

    def _map_logical_error(self, data: dict, response: httpx.Response, request: httpx.Request) -> None:
        # not actually sure this is necessary, so far all of them have been HttpStatusError
        data_status: int | None = data.get("Status") or data.get("status") or None

        if isinstance(data, dict) and isinstance(data_status, int) and not 200 <= data_status <= 299:
            LOGGER.error(f"API returned error: {data}")
            raise exc.OtfRequestError("Bad API response", None, response=response, request=request)

        raise exc.OtfRequestError(
            f"Logical error in API response: {data}", original_exception=None, response=response, request=request
        )

    def _handle_response(self, method: str, response: httpx.Response, request: httpx.Request) -> Any:  # noqa: ANN401
        if not response.text:
            if method == "GET":
                raise exc.OtfRequestError("Empty response", None, response=response, request=request)

            LOGGER.debug(f"No content returned from {method} {response.url}")
            return None

        try:
            json_data = response.json()
        except JSONDecodeError as e:
            LOGGER.error(f"Invalid JSON: {e}")
            LOGGER.error(f"Response content: {response.text}")
            raise

        if is_error_response(json_data):
            self._map_logical_error(json_data, response, request)

        return json_data
