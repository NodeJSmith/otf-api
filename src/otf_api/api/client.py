import atexit
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from json import JSONDecodeError
from logging import getLogger
from typing import Any, Self

import httpx
import pendulum
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yarl import URL

from otf_api import exceptions as exc
from otf_api.api.utils import get_json_from_response, is_error_response
from otf_api.auth import OtfUser
from otf_api.cache import CACHE

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json",
    "user-agent": "okhttp/4.12.0",
}
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

    def __eq__(self, other: Self | Any) -> bool:  # noqa: ANN401
        """Check if two Otf objects are equal."""
        if not isinstance(other, type(self)):
            return False
        return self.member_uuid == other.member_uuid

    def __hash__(self):
        """Return a hash value for the object."""
        # Combine immutable attributes into a single hash value
        return hash(self.member_uuid)

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


class BookingClient:
    """Client for managing bookings and classes in the OTF API.

    This class provides methods to retrieve classes, book classes, cancel bookings, and rate classes.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    def classes_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the classes API."""
        return self.client.do(method, API_IO_BASE_URL, path, params, headers=headers, **kwargs)

    def get_classes(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw class data."""
        return self.classes_request("GET", "/v1/classes", params={"studio_ids": studio_uuids})["items"]

    def delete_booking(self, booking_uuid: str) -> dict:
        """Cancel a booking by booking_uuid."""
        resp = self.client.default_request(
            "DELETE", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}", params={"confirmed": "true"}
        )

        return resp

    def put_class(self, body: dict) -> dict:
        """Book a class by class_uuid.

        Args:
            body (dict): The request body containing booking details.

        Returns:
            dict: The response from the booking request.

        Raises:
            AlreadyBookedError: If the class is already booked.
            OutsideSchedulingWindowError: If the class is outside the scheduling window.
            OtfException: If there is an error booking the class.
        """
        return self.client.default_request("PUT", f"/member/members/{self.member_uuid}/bookings", json=body)["data"]

    def post_class_new(self, body: dict[str, str | bool]) -> dict:
        """Book a class by class_id."""
        return self.classes_request("POST", "/v1/bookings/me", json=body)

    def get_booking(self, booking_uuid: str) -> dict:
        """Retrieve raw booking data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}")["data"]

    def get_bookings(self, start_date: str | None, end_date: str | None, status: str | list[str] | None) -> dict:
        """Retrieve raw bookings data."""
        if isinstance(status, list):
            status = ",".join(status)

        return self.client.default_request(
            "GET",
            f"/member/members/{self.member_uuid}/bookings",
            params={"startDate": start_date, "endDate": end_date, "statuses": status},
        )["data"]

    def get_bookings_new(
        self,
        ends_before: datetime,
        starts_after: datetime,
        include_canceled: bool = True,
        expand: bool = False,
    ) -> dict:
        """Retrieve raw bookings data."""
        params: dict[str, bool | str] = {
            "ends_before": pendulum.instance(ends_before).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "starts_after": pendulum.instance(starts_after).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        params["include_canceled"] = include_canceled if include_canceled is not None else True
        params["expand"] = expand if expand is not None else False

        return self.classes_request("GET", "/v1/bookings/me", params=params)["items"]

    def delete_booking_new(self, booking_id: str) -> None:
        """Cancel a booking by booking_id."""
        self.classes_request("DELETE", f"/v1/bookings/me/{booking_id}")

    def post_class_rating(
        self, class_uuid: str, performance_summary_id: str, class_rating: int, coach_rating: int
    ) -> dict:
        """Retrieve raw response from rating a class and coach."""
        return self.client.default_request(
            "POST",
            "/mobile/v1/members/classes/ratings",
            json={
                "classUUId": class_uuid,
                "otBeatClassHistoryUUId": performance_summary_id,
                "classRating": class_rating,
                "coachRating": coach_rating,
            },
        )


class WorkoutClient:
    """Client for retrieving workout and performance data from the OTF API.

    This class provides methods to access telemetry data, performance summaries, and workout history.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.user = client.user
        self.member_uuid = client.member_uuid

    def telemetry_request(
        self, method: str, path: str, params: dict[str, Any] | None = None, headers: dict[str, Any] | None = None
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the Telemetry API."""
        return self.client.do(method, API_TELEMETRY_BASE_URL, path, params, headers=headers)

    def performance_summary_request(
        self, method: str, path: str, params: dict[str, Any] | None = None, headers: dict[str, Any] | None = None
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the performance summary API."""
        perf_api_headers = {"koji-member-id": self.member_uuid, "koji-member-email": self.user.email_address}
        headers = perf_api_headers | (headers or {})
        return self.client.do(method, API_IO_BASE_URL, path, params, headers=headers)

    def get_member_lifetime_stats(self, select_time: str) -> dict:
        """Retrieve raw lifetime stats data."""
        return self.client.default_request("GET", f"/performance/v2/{self.member_uuid}/over-time/{select_time}")["data"]

    def get_out_of_studio_workout_history(self) -> dict:
        """Retrieve raw out-of-studio workout history data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/out-of-studio-workout")["data"]

    def get_performance_summaries(self, limit: int | None = None) -> dict:
        """Retrieve raw performance summaries data."""
        params = {"limit": limit} if limit else {}
        return self.performance_summary_request("GET", "/v1/performance-summaries", params=params)

    @CACHE.memoize(expire=600, tag="performance_summary", ignore=(0,))
    def get_performance_summary(self, performance_summary_id: str) -> dict:
        """Retrieve raw performance summary data."""
        return self.performance_summary_request("GET", f"/v1/performance-summaries/{performance_summary_id}")

    def get_hr_history_raw(self) -> dict:
        """Retrieve raw heart rate history."""
        return self.telemetry_request("GET", "/v1/physVars/maxHr/history", params={"memberUuid": self.member_uuid})[
            "history"
        ]

    @CACHE.memoize(expire=600, tag="telemetry", ignore=(0,))
    def get_telemetry(self, performance_summary_id: str, max_data_points: int = 150) -> dict:
        """Retrieve raw telemetry data."""
        return self.telemetry_request(
            "GET",
            "/v1/performance/summary",
            params={"classHistoryUuid": performance_summary_id, "maxDataPoints": max_data_points},
        )

    def get_body_composition_list(self) -> dict:
        """Retrieve raw body composition list."""
        return self.client.default_request("GET", f"/member/members/{self.user.cognito_id}/body-composition")["data"]

    def get_challenge_tracker(self) -> dict:
        """Retrieve raw challenge tracker data."""
        return self.client.default_request("GET", f"/challenges/v3.1/member/{self.member_uuid}")

    def get_benchmarks(self, challenge_category_id: int, equipment_id: int, challenge_subcategory_id: int) -> dict:
        """Retrieve raw fitness benchmark data."""
        return self.client.default_request(
            "GET",
            f"/challenges/v3/member/{self.member_uuid}/benchmarks",
            params={
                "equipmentId": equipment_id,
                "challengeTypeId": challenge_category_id,
                "challengeSubTypeId": challenge_subcategory_id,
            },
        )["Dto"]

    def get_challenge_tracker_detail(self, challenge_category_id: int) -> dict:
        """Retrieve raw challenge tracker detail data."""
        return self.client.default_request(
            "GET",
            f"/challenges/v1/member/{self.member_uuid}/participation",
            params={"challengeTypeId": challenge_category_id},
        )["Dto"]

    def get_perf_summary_to_class_uuid_mapping(self) -> dict[str, str | None]:
        """Get a mapping of performance summary IDs to class UUIDs. These will be used when rating a class.

        Returns:
            dict[str, str | None]: A dictionary mapping performance summary IDs to class UUIDs.
        """
        perf_summaries = self.get_performance_summaries()["items"]
        return {item["id"]: item["class"].get("ot_base_class_uuid") for item in perf_summaries}

    def get_perf_summaries_threaded(self, performance_summary_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Get performance summaries in a ThreadPoolExecutor, to speed up the process.

        Args:
            performance_summary_ids (list[str]): The performance summary IDs to get.

        Returns:
            dict[str, dict[str, Any]]: A dictionary of performance summaries, keyed by performance summary ID.
        """
        with ThreadPoolExecutor(max_workers=10) as pool:
            perf_summaries = pool.map(self.get_performance_summary, performance_summary_ids)

        perf_summaries_dict = {perf_summary["id"]: perf_summary for perf_summary in perf_summaries}
        return perf_summaries_dict

    def get_telemetry_threaded(
        self, performance_summary_ids: list[str], max_data_points: int = 150
    ) -> dict[str, dict[str, Any]]:
        """Get telemetry in a ThreadPoolExecutor, to speed up the process.

        Args:
            performance_summary_ids (list[str]): The performance summary IDs to get.
            max_data_points (int): The max data points to use for the telemetry. Default is 150.

        Returns:
            dict[str, Telemetry]: A dictionary of telemetry, keyed by performance summary ID.
        """
        partial_fn = partial(self.get_telemetry, max_data_points=max_data_points)
        with ThreadPoolExecutor(max_workers=10) as pool:
            telemetry = pool.map(partial_fn, performance_summary_ids)
        telemetry_dict = {perf_summary["classHistoryUuid"]: perf_summary for perf_summary in telemetry}
        return telemetry_dict

    def get_aspire_data(self, datetime: str | None, unit: str | None) -> dict:
        """Retrieve raw aspire wearable data."""
        return self.client.default_request(
            "GET", f"/member/wearables/{self.member_uuid}/wearable-daily", params={"datetime": datetime, "unit": unit}
        )


class StudioClient:
    """Client for retrieving studio and service data from the OTF API.

    This class provides methods to search for studios by geographic location, retrieve studio details,
    manage favorite studios, and get studio services.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    @CACHE.memoize(expire=600, tag="studio_detail", ignore=(0,))
    def get_studio_detail(self, studio_uuid: str) -> dict:
        """Retrieve raw studio details."""
        return self.client.default_request("GET", f"/mobile/v1/studios/{studio_uuid}")["data"]

    def _get_studios_by_geo(
        self, latitude: float | None, longitude: float | None, distance: int, page_index: int, page_size: int
    ) -> dict:
        """Retrieve raw studios by geo data."""
        return self.client.default_request(
            "GET",
            "/mobile/v1/studios",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "distance": distance,
                "pageIndex": page_index,
                "pageSize": page_size,
            },
        )

    def get_studios_by_geo(
        self, latitude: float | None, longitude: float | None, distance: int = 50
    ) -> list[dict[str, Any]]:
        """Searches for studios by geographic location.

        Args:
            latitude (float | None): Latitude of the location.
            longitude (float | None): Longitude of the location.
            distance (int): The distance in miles to search around the location. Default is 50.

        Returns:
            list[dict[str, Any]]: A list of studios within the specified distance from the given latitude and longitude.

        Raises:
            exc.OtfRequestError: If the request to the API fails.
        """
        distance = min(distance, 250)  # max distance is 250 miles
        page_size = 100
        page_index = 1
        LOGGER.debug(
            "Starting studio search",
            extra={
                "latitude": latitude,
                "longitude": longitude,
                "distance": distance,
                "page_index": page_index,
                "page_size": page_size,
            },
        )

        all_results: dict[str, dict[str, Any]] = {}

        while True:
            res = self._get_studios_by_geo(latitude, longitude, distance, page_index, page_size)

            studios = res["data"].get("studios", [])
            total_count = res["data"].get("pagination", {}).get("totalCount", 0)

            all_results.update({studio["studioUUId"]: studio for studio in studios})
            if len(all_results) >= total_count or not studios:
                break

            page_index += 1

        LOGGER.info("Studio search completed, fetched %d of %d studios", len(all_results), total_count, stacklevel=2)

        return list(all_results.values())

    def get_favorite_studios(self) -> dict:
        """Retrieve raw favorite studios data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/favorite-studios")["data"]

    def get_studio_services(self, studio_uuid: str) -> dict:
        """Retrieve raw studio services data."""
        return self.client.default_request("GET", f"/member/studios/{studio_uuid}/services")["data"]

    def post_favorite_studio(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from adding a studio to favorite studios."""
        return self.client.default_request(
            "POST", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids}
        )["data"]

    def delete_favorite_studio(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from removing a studio from favorite studios."""
        return self.client.default_request(
            "DELETE", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids}
        )

    def get_studio_detail_threaded(self, studio_uuids: list[str]) -> dict[str, dict[str, Any]]:
        """Get studio details in a ThreadPoolExecutor, to speed up the process.

        Args:
            studio_uuids (list[str]): The studio UUIDs to get.

        Returns:
            dict[str, dict[str, Any]]: A dictionary of studio details, keyed by studio UUID.
        """
        with ThreadPoolExecutor(max_workers=10) as pool:
            studios = pool.map(self.get_studio_detail, studio_uuids)

        studios_dict = {studio["studioUUId"]: studio for studio in studios}
        return studios_dict


class MemberClient:
    """Client for retrieving and managing member data in the OTF API.

    This class provides methods to access member details, membership information, notification settings,
    and member services. It also allows updating member information such as name and notification preferences.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    @CACHE.memoize(expire=600, tag="member_detail", ignore=(0,))
    def get_member_detail(self) -> dict:
        """Retrieve raw member details."""
        return self.client.default_request(
            "GET", f"/member/members/{self.member_uuid}", params={"include": "memberAddresses,memberClassSummary"}
        )["data"]

    def get_member_membership(self) -> dict:
        """Retrieve raw member membership details."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/memberships")["data"]

    def get_sms_notification_settings(self, phone_number: str) -> dict:
        """Retrieve raw SMS notification settings."""
        return self.client.default_request("GET", path="/sms/v1/preferences", params={"phoneNumber": phone_number})[
            "data"
        ]

    def get_email_notification_settings(self, email: str) -> dict:
        """Retrieve raw email notification settings."""
        return self.client.default_request("GET", path="/otfmailing/v2/preferences", params={"email": email})["data"]

    def get_member_services(self, active_only: bool) -> dict:
        """Retrieve raw member services data."""
        return self.client.default_request(
            "GET", f"/member/members/{self.member_uuid}/services", params={"activeOnly": str(active_only).lower()}
        )

    def get_member_purchases(self) -> dict:
        """Retrieve raw member purchases data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/purchases")["data"]

    def post_sms_notification_settings(
        self, phone_number: str, promotional_enabled: bool, transactional_enabled: bool
    ) -> dict:
        """Retrieve raw response from updating SMS notification settings.

        Warning:
            ---
            This endpoint seems to accept almost anything, converting values to truthy/falsey and
            updating the settings accordingly. The one error I've gotten is with -1

            ```
            ERROR - Response:
            {
            "code": "ER_WARN_DATA_OUT_OF_RANGE",
            "message": "An unexpected server error occurred, please try again.",
            "details": [
                    {
                "message": "ER_WARN_DATA_OUT_OF_RANGE: Out of range value for column 'IsPromotionalSMSOptIn' at row 1",
                "additionalInfo": ""
                    }
                ]
            }
            ```
        """
        return self.client.default_request(
            "POST",
            "/sms/v1/preferences",
            json={
                "promosms": promotional_enabled,
                "source": "OTF",
                "transactionalsms": transactional_enabled,
                "phoneNumber": phone_number,
            },
        )

    def post_email_notification_settings(
        self, email: str, promotional_enabled: bool, transactional_enabled: bool
    ) -> dict:
        """Retrieve raw response from updating email notification settings."""
        return self.client.default_request(
            "POST",
            "/otfmailing/v2/preferences",
            json={
                "promotionalEmail": promotional_enabled,
                "source": "OTF",
                "transactionalEmail": transactional_enabled,
                "email": email,
            },
        )

    def put_member_name(self, first_name: str, last_name: str) -> dict:
        """Retrieve raw response from updating member name."""
        CACHE.evict(tag="member_detail", retry=True)
        return self.client.default_request(
            "PUT",
            f"/member/members/{self.member_uuid}",
            json={"firstName": first_name, "lastName": last_name},
        )["data"]

    def get_app_config(self) -> dict[str, Any]:
        """Retrieve raw app configuration data.

        Returns:
            dict[str, Any]: A dictionary containing app configuration data.
        """
        return self.client.default_request("GET", "/member/app-configurations", headers={"SIGV4AUTH_REQUIRED": "true"})
