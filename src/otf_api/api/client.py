import atexit
import contextlib
import json
import os
import re
from json import JSONDecodeError
from logging import getLogger
from typing import Any, NoReturn

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yarl import URL

from otf_api import exceptions as exc
from otf_api.anonymize.hooks import create_capture_hook
from otf_api.api.utils import get_json_from_response, is_error_response
from otf_api.auth import OtfUser
from otf_api.cache import get_cache

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
API_GATEWAY_BASE_URL = "api.gateway.orangetheory.com"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json",
    "user-agent": "okhttp/4.12.0",
}
CACHE = get_cache()
LOGGER = getLogger(__name__)

# Maximum response body size (bytes) the library will attempt to parse.
# Protects against OOM from unexpectedly large API responses.
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB


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
        self.log_raw_response = os.getenv("OTF_LOG_RAW_RESPONSE", "false").lower() == "true"
        self._closed = False
        atexit.register(self.close)

        if os.getenv("OTF_ANONYMIZE_RESPONSES", "false").lower() == "true":
            if not os.getenv("OTF_ANONYMIZE_SEED") and self.member_uuid:
                with contextlib.suppress(ValueError):
                    os.environ["OTF_ANONYMIZE_SEED"] = str(int(self.member_uuid.replace("-", ""), 16) % (2**32))
            self._anonymize_hook = create_capture_hook()
            self.session.event_hooks["response"].append(self._anonymize_hook)

    def close(self) -> None:
        """Close the underlying HTTP session.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if not self._closed:
            self.session.close()
            self._closed = True

    def __getstate__(self):
        """Get the state of the OtfClient instance for serialization."""
        state = self.__dict__.copy()
        # Remove circular references
        state.pop("session", None)
        return state

    def __setstate__(self, state):  # noqa
        """Set the state of the OtfClient instance from serialized data."""
        self.__dict__.update(state)
        self.session = httpx.Client(
            headers=HEADERS, auth=self.user.httpx_auth, timeout=httpx.Timeout(20.0, connect=60.0)
        )
        self._closed = False
        atexit.register(self.close)

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
        retry=retry_if_exception_type((exc.RetryableOtfRequestError, exc.OtfTransportError)),
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
            OtfRequestError: If the request fails or the response is invalid (includes subclasses
                like ResourceNotFoundError, RetryableOtfRequestError, etc.).
        """
        full_url = str(URL.build(scheme="https", host=base_url, path=path))
        request = self._build_request(method, full_url, params, headers, **kwargs)
        LOGGER.debug("Making %r request to '%s'", method, str(request.url))

        try:
            response = self.session.send(request)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            json_data = get_json_from_response(e.response)
            self._map_http_error(json_data, e, e.response, request)
        except httpx.TransportError as e:
            LOGGER.warning("Transport error on %r %r: %s", request.method, request.url, e)
            raise exc.OtfTransportError(str(e)) from e
        except Exception as e:
            LOGGER.exception("Unexpected error during %r %r: %s - %s", request.method, request.url, type(e).__name__, e)
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
        """Perform an API request to the default OTF API base URL.

        This is a convenience wrapper around ``do()`` that uses ``API_BASE_URL`` as the base URL.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            path (str): The specific endpoint to request.
            params (dict[str, Any] | None): Query parameters to include in the request.
            headers (dict[str, Any] | None): Additional headers to include in the request.
            **kwargs: Additional keyword arguments to pass to the request.

        Returns:
            Any: The response data from the API request.

        Raises:
            OtfRequestError: If the request fails or the response is invalid.
        """
        return self.do(method, API_BASE_URL, path, params, headers=headers, **kwargs)

    def _map_http_error(
        self, data: dict, error: httpx.HTTPStatusError, response: httpx.Response, request: httpx.Request
    ) -> NoReturn:
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
                raise exc.ResourceNotFoundError("Booking was already cancelled")
            if error_code == "603":
                raise exc.AlreadyBookedError("Class is already booked")
            if error_code == "602":
                raise exc.OutsideSchedulingWindowError("Class is outside scheduling window")

        LOGGER.error("HTTP error %s for %s %s", response.status_code, request.method, request.url)
        error_cls = exc.RetryableOtfRequestError if response.status_code >= 500 else exc.OtfRequestError
        raise error_cls(
            message=f"HTTP error {response.status_code} for {request.method} {request.url}",
            original_exception=error,
            request=request,
            response=response,
        )

    def _map_logical_error(self, data: dict, response: httpx.Response, request: httpx.Request) -> None:
        # not actually sure this is necessary, so far all of them have been HttpStatusError
        data_status: int | None = data.get("Status") or data.get("status") or None

        if isinstance(data, dict) and isinstance(data_status, int) and not 200 <= data_status <= 299:
            LOGGER.error("API returned error: %s", data)
            raise exc.OtfRequestError("Bad API response", None, response=response, request=request)

        raise exc.OtfRequestError(
            f"Logical error in API response: {data}", original_exception=None, response=response, request=request
        )

    def _handle_response(self, method: str, response: httpx.Response, request: httpx.Request) -> Any:  # noqa: ANN401
        if not response.text:
            if method == "GET":
                raise exc.OtfRequestError("Empty response", None, response=response, request=request)

            LOGGER.debug("No content returned from %s %s", method, response.url)
            return None

        content_length = len(response.content)
        if content_length > MAX_RESPONSE_SIZE:
            LOGGER.error(
                "Response from %s %s exceeds size limit (%d bytes, max %d)",
                method,
                response.url,
                content_length,
                MAX_RESPONSE_SIZE,
            )
            raise exc.OtfRequestError(
                f"Response too large ({content_length} bytes, max {MAX_RESPONSE_SIZE})",
                original_exception=None,
                response=response,
                request=request,
            )

        try:
            json_data = response.json()
        except JSONDecodeError as e:
            LOGGER.error("Invalid JSON: %s", e)
            LOGGER.error("Response content: %s", response.text)
            raise

        if is_error_response(json_data):
            self._map_logical_error(json_data, response, request)

        if self.log_raw_response:
            LOGGER.debug("Response from %s %s: %s", method, response.url, json.dumps(json_data, indent=4))

        return json_data
