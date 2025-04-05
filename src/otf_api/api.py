import atexit
import contextlib
import functools
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date, datetime, timedelta
from json import JSONDecodeError
from logging import getLogger
from typing import Any, Literal

import attrs
import httpx
from cachetools import TTLCache, cached
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from yarl import URL

from otf_api import exceptions as exc
from otf_api import filters, models
from otf_api.auth import OtfUser
from otf_api.models.enums import HISTORICAL_BOOKING_STATUSES
from otf_api.utils import ensure_date, ensure_list, get_booking_uuid, get_class_uuid

API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
LOGGER = getLogger(__name__)


@attrs.define(init=False)
class Otf:
    member: models.MemberDetail
    member_uuid: str
    home_studio: models.StudioDetail
    home_studio_uuid: str
    user: OtfUser
    session: httpx.Client

    def __init__(self, user: OtfUser | None = None):
        """Initialize the OTF API client.

        Args:
            user (OtfUser): The user to authenticate as.
        """
        self.user = user or OtfUser()
        self.member_uuid = self.user.member_uuid

        self.session = httpx.Client(
            headers=JSON_HEADERS, auth=self.user.httpx_auth, timeout=httpx.Timeout(20.0, connect=60.0)
        )
        atexit.register(self.session.close)

        self.member = self.get_member_detail()
        self.home_studio = self.member.home_studio
        self.home_studio_uuid = self.home_studio.studio_uuid

    def __eq__(self, other):
        if not isinstance(other, Otf):
            return False
        return self.member_uuid == other.member_uuid

    def __hash__(self):
        # Combine immutable attributes into a single hash value
        return hash(self.member_uuid)

    @retry(
        retry=retry_if_exception_type(exc.OtfRequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _do(
        self,
        method: str,
        base_url: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Perform an API request."""

        headers = headers or {}
        params = params or {}
        params = {k: v for k, v in params.items() if v is not None}

        full_url = str(URL.build(scheme="https", host=base_url, path=url))

        LOGGER.debug(f"Making {method!r} request to {full_url}, params: {params}")

        request = self.session.build_request(method, full_url, headers=headers, params=params, **kwargs)
        response = self.session.send(request)

        try:
            response.raise_for_status()
        except httpx.RequestError as e:
            LOGGER.exception(f"Error making request: {e}")
            LOGGER.exception(f"Response: {response.text}")
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise exc.ResourceNotFoundError("Resource not found")

            if e.response.status_code == 403:
                raise

            raise exc.OtfRequestError("Error making request", e, response=response, request=request)
        except Exception as e:
            LOGGER.exception(f"Error making request: {e}")
            raise

        if not response.text:
            # insanely enough, at least one endpoint (get perf summary) returns None without error instead of 404
            raise exc.OtfRequestError("Empty response", None, response=response, request=request)

        try:
            resp = response.json()
        except JSONDecodeError as e:
            LOGGER.error(f"Error decoding JSON: {e}")
            LOGGER.error(f"Response: {response.text}")
            raise

        if (
            "Status" in resp
            and isinstance(resp["Status"], int)
            and not (resp["Status"] >= 200 and resp["Status"] <= 299)
        ):
            LOGGER.error(f"Error making request: {resp}")
            raise exc.OtfRequestError("Error making request", None, response=response, request=request)

        return resp

    def _classes_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the classes API."""
        return self._do(method, API_IO_BASE_URL, url, params)

    def _default_request(self, method: str, url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Perform an API request to the default API."""
        return self._do(method, API_BASE_URL, url, params, **kwargs)

    def _telemetry_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the Telemetry API."""
        return self._do(method, API_TELEMETRY_BASE_URL, url, params)

    def _performance_summary_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the performance summary API."""
        perf_api_headers = {"koji-member-id": self.member_uuid, "koji-member-email": self.user.email_address}
        return self._do(method, API_IO_BASE_URL, url, params, perf_api_headers)

    def _get_classes_raw(self, studio_uuids: list[str] | None) -> dict:
        """Retrieve raw class data."""
        return self._classes_request("GET", "/v1/classes", params={"studio_ids": studio_uuids})

    def _get_booking_raw(self, booking_uuid: str) -> dict:
        """Retrieve raw booking data."""
        return self._default_request("GET", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}")

    def _get_bookings_raw(self, start_date: str | None, end_date: str | None, status: str | list[str] | None) -> dict:
        """Retrieve raw bookings data."""

        if isinstance(status, list):
            status = ",".join(status)

        return self._default_request(
            "GET",
            f"/member/members/{self.member_uuid}/bookings",
            params={"startDate": start_date, "endDate": end_date, "statuses": status},
        )

    def _get_member_detail_raw(self) -> dict:
        """Retrieve raw member details."""
        return self._default_request(
            "GET", f"/member/members/{self.member_uuid}", params={"include": "memberAddresses,memberClassSummary"}
        )

    def _get_member_membership_raw(self) -> dict:
        """Retrieve raw member membership details."""
        return self._default_request("GET", f"/member/members/{self.member_uuid}/memberships")

    def _get_performance_summaries_raw(self, limit: int | None = None) -> dict:
        """Retrieve raw performance summaries data."""
        params = {"limit": limit} if limit else {}
        return self._performance_summary_request("GET", "/v1/performance-summaries", params=params)

    def _get_performance_summary_raw(self, performance_summary_id: str) -> dict:
        """Retrieve raw performance summary data."""
        return self._performance_summary_request("GET", f"/v1/performance-summaries/{performance_summary_id}")

    def _get_hr_history_raw(self) -> dict:
        """Retrieve raw heart rate history."""
        return self._telemetry_request("GET", "/v1/physVars/maxHr/history", params={"memberUuid": self.member_uuid})

    def _get_telemetry_raw(self, performance_summary_id: str, max_data_points: int) -> dict:
        """Retrieve raw telemetry data."""
        return self._telemetry_request(
            "GET",
            "/v1/performance/summary",
            params={"classHistoryUuid": performance_summary_id, "maxDataPoints": max_data_points},
        )

    def _get_studio_detail_raw(self, studio_uuid: str) -> dict:
        """Retrieve raw studio details."""
        return self._default_request("GET", f"/mobile/v1/studios/{studio_uuid}")

    def _get_studios_by_geo_raw(
        self, latitude: float | None, longitude: float | None, distance: int, page_index: int, page_size: int
    ) -> dict:
        """Retrieve raw studios by geo data."""
        return self._default_request(
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

    def _get_body_composition_list_raw(self) -> dict:
        """Retrieve raw body composition list."""
        return self._default_request("GET", f"/member/members/{self.user.cognito_id}/body-composition")

    def _get_challenge_tracker_raw(self) -> dict:
        """Retrieve raw challenge tracker data."""
        return self._default_request("GET", f"/challenges/v3.1/member/{self.member_uuid}")

    def _get_benchmarks_raw(self, challenge_category_id: int, equipment_id: int, challenge_subcategory_id: int) -> dict:
        """Retrieve raw fitness benchmark data."""
        return self._default_request(
            "GET",
            f"/challenges/v3/member/{self.member_uuid}/benchmarks",
            params={
                "equipmentId": equipment_id,
                "challengeTypeId": challenge_category_id,
                "challengeSubTypeId": challenge_subcategory_id,
            },
        )

    def _get_sms_notification_settings_raw(self) -> dict:
        """Retrieve raw SMS notification settings."""
        return self._default_request("GET", url="/sms/v1/preferences", params={"phoneNumber": self.member.phone_number})

    def _get_email_notification_settings_raw(self) -> dict:
        """Retrieve raw email notification settings."""
        return self._default_request("GET", url="/otfmailing/v2/preferences", params={"email": self.member.email})

    def _get_member_lifetime_stats_raw(self, select_time: str) -> dict:
        """Retrieve raw lifetime stats data."""
        return self._default_request("GET", f"/performance/v2/{self.member_uuid}/over-time/{select_time}")

    def _get_member_services_raw(self, active_only: bool) -> dict:
        """Retrieve raw member services data."""
        return self._default_request(
            "GET", f"/member/members/{self.member_uuid}/services", params={"activeOnly": str(active_only).lower()}
        )

    def _get_aspire_data_raw(self, datetime: str | None, unit: str | None) -> dict:
        """Retrieve raw aspire wearable data."""
        return self._default_request(
            "GET", f"/member/wearables/{self.member_uuid}/wearable-daily", params={"datetime": datetime, "unit": unit}
        )

    def _get_member_purchases_raw(self) -> dict:
        """Retrieve raw member purchases data."""
        return self._default_request("GET", f"/member/members/{self.member_uuid}/purchases")

    def _get_favorite_studios_raw(self) -> dict:
        """Retrieve raw favorite studios data."""
        return self._default_request("GET", f"/member/members/{self.member_uuid}/favorite-studios")

    def _get_studio_services_raw(self, studio_uuid: str) -> dict:
        """Retrieve raw studio services data."""
        return self._default_request("GET", f"/member/studios/{studio_uuid}/services")

    def _get_out_of_studio_workout_history_raw(self) -> dict:
        """Retrieve raw out-of-studio workout history data."""
        return self._default_request("GET", f"/member/members/{self.member_uuid}/out-of-studio-workout")

    def _add_favorite_studio_raw(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from adding a studio to favorite studios."""
        return self._default_request("POST", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids})

    def _remove_favorite_studio_raw(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw response from removing a studio from favorite studios."""
        return self._default_request(
            "DELETE", "/mobile/v1/members/favorite-studios", json={"studioUUIds": studio_uuids}
        )

    def _get_challenge_tracker_detail_raw(self, challenge_category_id: int) -> dict:
        """Retrieve raw challenge tracker detail data."""
        return self._default_request(
            "GET",
            f"/challenges/v1/member/{self.member_uuid}/participation",
            params={"challengeTypeId": challenge_category_id},
        )

    def _update_sms_notification_settings_raw(self, promotional_enabled: bool, transactional_enabled: bool) -> dict:
        """Retrieve raw response from updating SMS notification settings."""
        return self._default_request(
            "POST",
            "/sms/v1/preferences",
            json={
                "promosms": promotional_enabled,
                "source": "OTF",
                "transactionalsms": transactional_enabled,
                "phoneNumber": self.member.phone_number,
            },
        )

    def _update_email_notification_settings_raw(self, promotional_enabled: bool, transactional_enabled: bool) -> dict:
        """Retrieve raw response from updating email notification settings."""
        return self._default_request(
            "POST",
            "/otfmailing/v2/preferences",
            json={
                "promotionalEmail": promotional_enabled,
                "source": "OTF",
                "transactionalEmail": transactional_enabled,
                "email": self.member.email,
            },
        )

    def _rate_class_raw(
        self, class_uuid: str, performance_summary_id: str, class_rating: int, coach_rating: int
    ) -> dict:
        """Retrieve raw response from rating a class and coach."""
        return self._default_request(
            "POST",
            "/mobile/v1/members/classes/ratings",
            json={
                "classUUId": class_uuid,
                "otBeatClassHistoryUUId": performance_summary_id,
                "classRating": class_rating,
                "coachRating": coach_rating,
            },
        )

    def _update_member_name_raw(self, first_name: str, last_name: str) -> dict:
        """Retrieve raw response from updating member name."""
        return self._default_request(
            "PUT",
            f"/member/members/{self.member_uuid}",
            json={"firstName": first_name, "lastName": last_name},
        )

    def get_classes(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        studio_uuids: list[str] | None = None,
        include_home_studio: bool | None = None,
        filters: list[filters.ClassFilter] | filters.ClassFilter | None = None,
    ) -> list[models.OtfClass]:
        """Get the classes for the user.

        Returns a list of classes that are available for the user, based on the studio UUIDs provided. If no studio
        UUIDs are provided, it will default to the user's home studio.

        Args:
            start_date (date | None): The start date for the classes. Default is None.
            end_date (date | None): The end date for the classes. Default is None.
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will\
            default to the user's home studio only.
            include_home_studio (bool): Whether to include the home studio in the classes. Default is True.
            filters (list[ClassFilter] | ClassFilter | None): A list of filters to apply to the classes, or a single\
            filter. Filters are applied as an OR operation. Default is None.

        Returns:
            list[OtfClass]: The classes for the user.
        """

        classes = self._get_classes(studio_uuids, include_home_studio)

        # remove those that are cancelled *by the studio*
        classes = [c for c in classes if not c.is_cancelled]

        bookings = self.get_bookings(status=models.BookingStatus.Booked)
        booked_classes = {b.class_uuid for b in bookings}

        for otf_class in classes:
            otf_class.is_booked = otf_class.class_uuid in booked_classes

        # filter by provided start_date/end_date, if provided
        classes = self._filter_classes_by_date(classes, start_date, end_date)

        # filter by provided filters, if provided
        classes = self._filter_classes_by_filters(classes, filters)

        # sort by start time, then by name
        classes = sorted(classes, key=lambda x: (x.starts_at, x.name))

        return classes

    def _get_classes(
        self, studio_uuids: list[str] | None = None, include_home_studio: bool | None = None
    ) -> list[models.OtfClass]:
        """Handles the actual request to get classes.

        Args:
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will\
            default to the user's home studio only.
            include_home_studio (bool): Whether to include the home studio in the classes. Default is True.

        Returns:
            list[OtfClass]: The classes for the user.
        """

        studio_uuids = ensure_list(studio_uuids) or [self.home_studio_uuid]
        studio_uuids = list(set(studio_uuids))  # remove duplicates

        if len(studio_uuids) > 50:
            LOGGER.warning("Cannot request classes for more than 50 studios at a time.")
            studio_uuids = studio_uuids[:50]

        if include_home_studio and self.home_studio_uuid not in studio_uuids:
            if len(studio_uuids) == 50:
                LOGGER.warning("Cannot include home studio, request already includes 50 studios.")
            else:
                studio_uuids.append(self.home_studio_uuid)

        classes_resp = self._get_classes_raw(studio_uuids)

        studio_dict = {s: self.get_studio_detail(s) for s in studio_uuids}
        classes: list[models.OtfClass] = []

        for c in classes_resp["items"]:
            c["studio"] = studio_dict[c["studio"]["id"]]  # the one (?) place where ID actually means UUID
            c["is_home_studio"] = c["studio"].studio_uuid == self.home_studio_uuid
            classes.append(models.OtfClass(**c))

        return classes

    def _filter_classes_by_date(
        self, classes: list[models.OtfClass], start_date: date | None, end_date: date | None
    ) -> list[models.OtfClass]:
        """Filter classes by start and end dates, as well as the max date the booking endpoint will accept.

        Args:
            classes (list[OtfClass]): The classes to filter.
            start_date (date | None): The start date to filter by.
            end_date (date | None): The end date to filter by.

        Returns:
            list[OtfClass]: The filtered classes.
        """

        # this endpoint returns classes that the `book_class` endpoint will reject, this filters them out
        max_date = datetime.today().date() + timedelta(days=29)

        classes = [c for c in classes if c.starts_at.date() <= max_date]

        # if not start date or end date, we're done
        if not start_date and not end_date:
            return classes

        if start_date := ensure_date(start_date):
            classes = [c for c in classes if c.starts_at.date() >= start_date]

        if end_date := ensure_date(end_date):
            classes = [c for c in classes if c.starts_at.date() <= end_date]

        return classes

    def _filter_classes_by_filters(
        self, classes: list[models.OtfClass], filters: list[filters.ClassFilter] | filters.ClassFilter | None
    ) -> list[models.OtfClass]:
        """Filter classes by the provided filters.

        Args:
            classes (list[OtfClass]): The classes to filter.
            filters (list[ClassFilter] | ClassFilter | None): The filters to apply.

        Returns:
            list[OtfClass]: The filtered classes.
        """
        if not filters:
            return classes

        filters = ensure_list(filters)
        filtered_classes: list[models.OtfClass] = []

        # apply each filter as an OR operation
        for f in filters:
            filtered_classes.extend(f.filter_classes(classes))

        # remove duplicates
        classes = list({c.class_uuid: c for c in filtered_classes}.values())

        return classes

    def get_booking(self, booking_uuid: str) -> models.Booking:
        """Get a specific booking by booking_uuid.

        Args:
            booking_uuid (str): The booking UUID to get.

        Returns:
            BookingList: The booking.

        Raises:
            ValueError: If booking_uuid is None or empty string.
        """
        if not booking_uuid:
            raise ValueError("booking_uuid is required")

        data = self._get_booking_raw(booking_uuid)
        return models.Booking(**data["data"])

    def get_booking_from_class(self, otf_class: str | models.OtfClass) -> models.Booking:
        """Get a specific booking by class_uuid or OtfClass object.

        Args:
            otf_class (str | OtfClass): The class UUID or the OtfClass object to get the booking for.

        Returns:
            Booking: The booking.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If class_uuid is None or empty string.
        """

        class_uuid = get_class_uuid(otf_class)

        all_bookings = self.get_bookings(exclude_cancelled=False, exclude_checkedin=False)

        if booking := next((b for b in all_bookings if b.class_uuid == class_uuid), None):
            return booking

        raise exc.BookingNotFoundError(f"Booking for class {class_uuid} not found.")

    def book_class(self, otf_class: str | models.OtfClass) -> models.Booking:
        """Book a class by providing either the class_uuid or the OtfClass object.

        Args:
            otf_class (str | OtfClass): The class UUID or the OtfClass object to book.

        Returns:
            Booking: The booking.

        Raises:
            AlreadyBookedError: If the class is already booked.
            OutsideSchedulingWindowError: If the class is outside the scheduling window.
            ValueError: If class_uuid is None or empty string.
            OtfException: If there is an error booking the class.
        """

        class_uuid = get_class_uuid(otf_class)

        self._check_class_already_booked(class_uuid)

        if isinstance(otf_class, models.OtfClass):
            self._check_for_booking_conflicts(otf_class)

        body = {"classUUId": class_uuid, "confirmed": False, "waitlist": False}

        try:
            resp = self._default_request("PUT", f"/member/members/{self.member_uuid}/bookings", json=body)
        except exc.OtfRequestError as e:
            resp_obj = e.response.json()

            if resp_obj["code"] == "ERROR":
                err_code = resp_obj["data"]["errorCode"]
                if err_code == "603":
                    raise exc.AlreadyBookedError(f"Class {class_uuid} is already booked.")
                if err_code == "602":
                    raise exc.OutsideSchedulingWindowError(f"Class {class_uuid} is outside the scheduling window.")

            raise
        except Exception as e:
            raise exc.OtfException(f"Error booking class {class_uuid}: {e}")

        # get the booking uuid - we will only use this to return a Booking object using `get_booking`
        # this is an attempt to improve on OTF's terrible data model
        booking_uuid = resp["data"]["savedBookings"][0]["classBookingUUId"]

        booking = self.get_booking(booking_uuid)

        return booking

    def _check_class_already_booked(self, class_uuid: str) -> None:
        """Check if the class is already booked.

        Args:
            class_uuid (str): The class UUID to check.

        Raises:
            AlreadyBookedError: If the class is already booked.
        """
        existing_booking = None

        with contextlib.suppress(exc.BookingNotFoundError):
            existing_booking = self.get_booking_from_class(class_uuid)

        if not existing_booking:
            return

        if existing_booking.status != models.BookingStatus.Cancelled:
            raise exc.AlreadyBookedError(
                f"Class {class_uuid} is already booked.", booking_uuid=existing_booking.booking_uuid
            )

    def _check_for_booking_conflicts(self, otf_class: models.OtfClass) -> None:
        """Check for booking conflicts with the provided class.

        Checks the member's bookings to see if the provided class overlaps with any existing bookings. If a conflict is
        found, a ConflictingBookingError is raised.
        """

        bookings = self.get_bookings(start_date=otf_class.starts_at.date(), end_date=otf_class.starts_at.date())
        if not bookings:
            return

        for booking in bookings:
            booking_start = booking.otf_class.starts_at
            booking_end = booking.otf_class.ends_at
            # Check for overlap
            if not (otf_class.ends_at < booking_start or otf_class.starts_at > booking_end):
                raise exc.ConflictingBookingError(
                    f"You already have a booking that conflicts with this class ({booking.otf_class.class_uuid}).",
                    booking_uuid=booking.booking_uuid,
                )

    def cancel_booking(self, booking: str | models.Booking) -> None:
        """Cancel a booking by providing either the booking_uuid or the Booking object.

        Args:
            booking (str | Booking): The booking UUID or the Booking object to cancel.

        Raises:
            ValueError: If booking_uuid is None or empty string
            BookingNotFoundError: If the booking does not exist.
        """
        booking_uuid = get_booking_uuid(booking)

        try:
            self.get_booking(booking_uuid)
        except Exception:
            raise exc.BookingNotFoundError(f"Booking {booking_uuid} does not exist.")

        params = {"confirmed": "true"}
        resp = self._default_request(
            "DELETE", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}", params=params
        )
        if resp["code"] == "NOT_AUTHORIZED" and resp["message"].startswith("This class booking has"):
            raise exc.BookingAlreadyCancelledError(
                f"Booking {booking_uuid} is already cancelled.", booking_uuid=booking_uuid
            )

    def get_bookings(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        status: models.BookingStatus | list[models.BookingStatus] | None = None,
        exclude_cancelled: bool = True,
        exclude_checkedin: bool = True,
    ) -> list[models.Booking]:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | list[BookingStatus] | None): The status(es) to filter by. Default is None.
            exclude_cancelled (bool): Whether to exclude cancelled bookings. Default is True.
            exclude_checkedin (bool): Whether to exclude checked-in bookings. Default is True.

        Returns:
            list[Booking]: The member's bookings.

        Warning:
            ---
            Incorrect statuses do not cause any bad status code, they just return no results.

        Tip:
            ---
            `CheckedIn` - you must provide dates if you want to get bookings with a status of CheckedIn. If you do not
            provide dates, the endpoint will return no results for this status.

        Dates Notes:
            ---
            If dates are provided, the endpoint will return bookings where the class date is within the provided
            date range. If no dates are provided, it will go back 45 days and forward about 30 days.
        """

        if exclude_cancelled and status == models.BookingStatus.Cancelled:
            LOGGER.warning(
                "Cannot exclude cancelled bookings when status is Cancelled. Setting exclude_cancelled to False."
            )
            exclude_cancelled = False

        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        if isinstance(status, list):
            status_value = ",".join(status)
        elif isinstance(status, models.BookingStatus):
            status_value = status.value
        elif isinstance(status, str):
            status_value = status
        else:
            status_value = None

        resp = self._get_bookings_raw(start_date, end_date, status_value)["data"]

        # add studio details for each booking, instead of using the different studio model returned by this endpoint
        studio_uuids = {b["class"]["studio"]["studioUUId"] for b in resp}
        studios = {studio_uuid: self.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids}

        for b in resp:
            b["class"]["studio"] = studios[b["class"]["studio"]["studioUUId"]]
            b["is_home_studio"] = b["class"]["studio"].studio_uuid == self.home_studio_uuid

        bookings = [models.Booking(**b) for b in resp]
        bookings = sorted(bookings, key=lambda x: x.otf_class.starts_at)

        if exclude_cancelled:
            bookings = [b for b in bookings if b.status != models.BookingStatus.Cancelled]

        if exclude_checkedin:
            bookings = [b for b in bookings if b.status != models.BookingStatus.CheckedIn]

        return bookings

    def get_historical_bookings(self) -> list[models.Booking]:
        """Get the member's historical bookings. This will go back 45 days and return all bookings
        for that time period.

        Returns:
            list[Booking]: The member's historical bookings.
        """
        # api goes back 45 days but we'll go back 47 to be safe
        start_date = datetime.today().date() - timedelta(days=47)
        end_date = datetime.today().date()

        return self.get_bookings(
            start_date=start_date,
            end_date=end_date,
            status=HISTORICAL_BOOKING_STATUSES,
            exclude_cancelled=False,
            exclude_checkedin=False,
        )

    def get_member_detail(self) -> models.MemberDetail:
        """Get the member details.

        Returns:
            MemberDetail: The member details.
        """

        resp = self._get_member_detail_raw()
        data = resp["data"]

        # use standard StudioDetail model instead of the one returned by this endpoint
        home_studio_uuid = data["homeStudio"]["studioUUId"]
        data["home_studio"] = self.get_studio_detail(home_studio_uuid)

        return models.MemberDetail(**data)

    def get_member_membership(self) -> models.MemberMembership:
        """Get the member's membership details.

        Returns:
            MemberMembership: The member's membership details.
        """

        data = self._get_member_membership_raw()
        return models.MemberMembership(**data["data"])

    def get_member_purchases(self) -> list[models.MemberPurchase]:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            list[MemberPurchase]: The member's purchases.
        """
        purchases = self._get_member_purchases_raw()["data"]

        for p in purchases:
            p["studio"] = self.get_studio_detail(p["studio"]["studioUUId"])

        return [models.MemberPurchase(**purchase) for purchase in purchases]

    def _get_member_lifetime_stats(
        self, select_time: models.StatsTime = models.StatsTime.AllTime
    ) -> models.StatsResponse:
        """Get the member's lifetime stats.

        Args:
            select_time (StatsTime): The time period to get stats for. Default is StatsTime.AllTime.

        Notes:
            ---
            The time period provided in the path does not do anything, and the endpoint always returns the same data.
            It is being provided anyway, in case this changes in the future.

        Returns:
            Any: The member's lifetime stats.
        """

        data = self._get_member_lifetime_stats_raw(select_time.value)

        stats = models.StatsResponse(**data["data"])

        return stats

    def get_member_lifetime_stats_in_studio(
        self, select_time: models.StatsTime = models.StatsTime.AllTime
    ) -> models.TimeStats:
        """Get the member's lifetime stats in studio.

        Args:
            select_time (StatsTime): The time period to get stats for. Default is StatsTime.AllTime.

        Returns:
            Any: The member's lifetime stats in studio.
        """

        data = self._get_member_lifetime_stats(select_time)

        return data.in_studio.get_by_time(select_time)

    def get_member_lifetime_stats_out_of_studio(
        self, select_time: models.StatsTime = models.StatsTime.AllTime
    ) -> models.TimeStats:
        """Get the member's lifetime stats out of studio.

        Args:
            select_time (StatsTime): The time period to get stats for. Default is StatsTime.AllTime.

        Returns:
            Any: The member's lifetime stats out of studio.
        """

        data = self._get_member_lifetime_stats(select_time)

        return data.out_studio.get_by_time(select_time)

    def get_out_of_studio_workout_history(self) -> list[models.OutOfStudioWorkoutHistory]:
        """Get the member's out of studio workout history.

        Returns:
            list[OutOfStudioWorkoutHistory]: The member's out of studio workout history.
        """
        data = self._get_out_of_studio_workout_history_raw()

        return [models.OutOfStudioWorkoutHistory(**workout) for workout in data["data"]]

    def get_favorite_studios(self) -> list[models.StudioDetail]:
        """Get the member's favorite studios.

        Returns:
            list[StudioDetail]: The member's favorite studios.
        """
        data = self._get_favorite_studios_raw()
        studio_uuids = [studio["studioUUId"] for studio in data["data"]]
        return [self.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids]

    def add_favorite_studio(self, studio_uuids: list[str] | str) -> list[models.StudioDetail]:
        """Add a studio to the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to add to the member's favorite\
            studios. If a string is provided, it will be converted to a list.

        Returns:
            list[StudioDetail]: The new favorite studios.
        """
        studio_uuids = ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        resp = self._add_favorite_studio_raw(studio_uuids)

        new_faves = resp.get("data", {}).get("studios", [])

        return [models.StudioDetail(**studio) for studio in new_faves]

    def remove_favorite_studio(self, studio_uuids: list[str] | str) -> None:
        """Remove a studio from the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to remove from the member's\
            favorite studios. If a string is provided, it will be converted to a list.

        Returns:
            None
        """
        studio_uuids = ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        # keeping the convention of regular/raw methods even though this method doesn't return anything
        # in case that changes in the future
        self._remove_favorite_studio_raw(studio_uuids)

    def get_studio_services(self, studio_uuid: str | None = None) -> list[models.StudioService]:
        """Get the services available at a specific studio. If no studio UUID is provided, the member's home studio
        will be used.

        Args:
            studio_uuid (str, optional): The studio UUID to get services for.

        Returns:
            list[StudioService]: The services available at the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid
        data = self._get_studio_services_raw(studio_uuid)

        for d in data["data"]:
            d["studio"] = self.get_studio_detail(studio_uuid)

        return [models.StudioService(**d) for d in data["data"]]

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def get_studio_detail(self, studio_uuid: str | None = None) -> models.StudioDetail:
        """Get detailed information about a specific studio. If no studio UUID is provided, it will default to the
        user's home studio.

        If the studio is not found, it will return a StudioDetail object with default values.

        Args:
            studio_uuid (str, optional): The studio UUID to get detailed information about.

        Returns:
            StudioDetail: Detailed information about the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid

        try:
            res = self._get_studio_detail_raw(studio_uuid)
        except exc.ResourceNotFoundError:
            return models.StudioDetail(studioUUId=studio_uuid, studioName="Studio Not Found", studioStatus="Unknown")

        return models.StudioDetail(**res["data"])

    def get_studios_by_geo(
        self, latitude: float | None = None, longitude: float | None = None
    ) -> list[models.StudioDetail]:
        """Alias for search_studios_by_geo."""

        return self.search_studios_by_geo(latitude, longitude)

    def search_studios_by_geo(
        self, latitude: float | None = None, longitude: float | None = None, distance: int = 50
    ) -> list[models.StudioDetail]:
        """Search for studios by geographic location.

        Args:
            latitude (float, optional): Latitude of the location to search around, if None uses home studio latitude.
            longitude (float, optional): Longitude of the location to search around, if None uses home studio longitude.
            distance (int, optional): The distance in miles to search around the location. Default is 50.

        Returns:
            list[StudioDetail]: List of studios that match the search criteria.
        """
        latitude = latitude or self.home_studio.location.latitude
        longitude = longitude or self.home_studio.location.longitude

        return self._get_studios_by_geo(latitude, longitude, distance)

    def _get_all_studios(self) -> list[models.StudioDetail]:
        """Gets all studios. Marked as private to avoid random users calling it. Useful for testing and validating
        models.

        Returns:
            list[StudioDetail]: List of studios that match the search criteria.
        """
        # long/lat being None will cause the endpoint to return all studios
        return self._get_studios_by_geo(None, None)

    def _get_studios_by_geo(
        self, latitude: float | None, longitude: float | None, distance: int = 50
    ) -> list[models.StudioDetail]:
        """
        Searches for studios by geographic location.

        Args:
            latitude (float | None): Latitude of the location.
            longitude (float | None): Longitude of the location.

        Returns:
            list[models.StudioDetail]: List of studios matching the search criteria.
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
            res = self._get_studios_by_geo_raw(latitude, longitude, distance, page_index, page_size)

            studios = res["data"].get("studios", [])
            total_count = res["data"].get("pagination", {}).get("totalCount", 0)

            all_results.update({studio["studioUUId"]: studio for studio in studios})
            if len(all_results) >= total_count or not studios:
                break

            page_index += 1

        LOGGER.info("Studio search completed, fetched %d of %d studios", len(all_results), total_count, stacklevel=2)

        return [models.StudioDetail(**studio) for studio in all_results.values()]

    def get_body_composition_list(self) -> list[models.BodyCompositionData]:
        """Get the member's body composition list.

        Returns:
            list[BodyCompositionData]: The member's body composition list.
        """
        data = self._get_body_composition_list_raw()
        return [models.BodyCompositionData(**item) for item in data["data"]]

    def get_challenge_tracker(self) -> models.ChallengeTracker:
        """Get the member's challenge tracker content.

        Returns:
            ChallengeTracker: The member's challenge tracker content.
        """
        data = self._get_challenge_tracker_raw()
        return models.ChallengeTracker(**data["Dto"])

    def get_benchmarks(
        self,
        challenge_category_id: models.ChallengeCategory | Literal[0] = 0,
        equipment_id: models.EquipmentType | Literal[0] = 0,
        challenge_subcategory_id: int = 0,
    ) -> list[models.FitnessBenchmark]:
        """Get the member's challenge tracker participation details.

        Args:
            challenge_category_id (ChallengeType): The challenge type ID.
            equipment_id (EquipmentType | Literal[0]): The equipment ID, default is 0 - this doesn't seem\
                to be have any impact on the results.
            challenge_subcategory_id (int): The challenge sub type ID. Default is 0 - this doesn't seem\
                to be have any impact on the results.

        Returns:
            list[FitnessBenchmark]: The member's challenge tracker details.
        """
        data = self._get_benchmarks_raw(int(challenge_category_id), int(equipment_id), challenge_subcategory_id)
        return [models.FitnessBenchmark(**item) for item in data["Dto"]]

    def get_benchmarks_by_equipment(self, equipment_id: models.EquipmentType) -> list[models.FitnessBenchmark]:
        """Get the member's challenge tracker participation details by equipment.

        Args:
            equipment_id (EquipmentType): The equipment type ID.

        Returns:
            list[FitnessBenchmark]: The member's challenge tracker details.
        """
        benchmarks = self.get_benchmarks(equipment_id=equipment_id)

        benchmarks = [b for b in benchmarks if b.equipment_id == equipment_id]

        return benchmarks

    def get_benchmarks_by_challenge_category(
        self, challenge_category_id: models.ChallengeCategory
    ) -> list[models.FitnessBenchmark]:
        """Get the member's challenge tracker participation details by challenge.

        Args:
            challenge_category_id (ChallengeType): The challenge type ID.

        Returns:
            list[FitnessBenchmark]: The member's challenge tracker details.
        """
        benchmarks = self.get_benchmarks(challenge_category_id=challenge_category_id)

        benchmarks = [b for b in benchmarks if b.challenge_category_id == challenge_category_id]

        return benchmarks

    def get_challenge_tracker_detail(self, challenge_category_id: models.ChallengeCategory) -> models.FitnessBenchmark:
        """Get details about a challenge. This endpoint does not (usually) return member participation, but rather
        details about the challenge itself.

        Args:
            challenge_category_id (ChallengeType): The challenge type ID.

        Returns:
            FitnessBenchmark: Details about the challenge.
        """

        data = self._get_challenge_tracker_detail_raw(int(challenge_category_id))

        if len(data["Dto"]) > 1:
            LOGGER.warning("Multiple challenge participations found, returning the first one.")

        if len(data["Dto"]) == 0:
            raise exc.ResourceNotFoundError(f"Challenge {challenge_category_id} not found")

        return models.FitnessBenchmark(**data["Dto"][0])

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def get_performance_summaries_dict(self, limit: int | None = None) -> dict[str, models.PerformanceSummary]:
        """Get a dictionary of performance summaries for the authenticated user.

        Args:
            limit (int | None): The maximum number of entries to return. Default is None.

        Returns:
            dict[str, PerformanceSummary]: A dictionary of performance summaries, keyed by class history UUID.

        Developer Notes:
            ---
            In the app, this is referred to as 'getInStudioWorkoutHistory'.

        """

        items = self._get_performance_summaries_raw(limit=limit)["items"]

        distinct_studio_ids = set([rec["class"]["studio"]["id"] for rec in items])
        perf_summary_ids = set([rec["id"] for rec in items])

        with ThreadPoolExecutor() as pool:
            studio_futures = {s: pool.submit(self.get_studio_detail, s) for s in distinct_studio_ids}
            perf_summary_futures = {s: pool.submit(self._get_performancy_summary_detail, s) for s in perf_summary_ids}

            studio_dict = {k: v.result() for k, v in studio_futures.items()}
            # deepcopy these so that mutating them in PerformanceSummary doesn't affect the cache
            perf_summary_dict = {k: deepcopy(v.result()) for k, v in perf_summary_futures.items()}

        for item in items:
            item["class"]["studio"] = studio_dict[item["class"]["studio"]["id"]]
            item["detail"] = perf_summary_dict[item["id"]]

        entries = [models.PerformanceSummary(**item) for item in items]
        entries_dict = {entry.performance_summary_id: entry for entry in entries}

        return entries_dict

    def get_performance_summaries(self, limit: int | None = None) -> list[models.PerformanceSummary]:
        """Get a list of all performance summaries for the authenticated user.

        Args:
            limit (int | None): The maximum number of entries to return. Default is None.

        Returns:
            list[PerformanceSummary]: A list of performance summaries.

        Developer Notes:
            ---
            In the app, this is referred to as 'getInStudioWorkoutHistory'.

        """

        records = list(self.get_performance_summaries_dict(limit=limit).values())

        sorted_records = sorted(records, key=lambda x: x.otf_class.starts_at, reverse=True)

        return sorted_records

    def get_performance_summary(
        self, performance_summary_id: str, limit: int | None = None
    ) -> models.PerformanceSummary:
        """Get performance summary for a given workout.

        Note: Due to the way the OTF API is set up, we have to call both the list and the get endpoints. By
        default this will call the list endpoint with no limit, in order to ensure that the performance summary
        is returned if it exists. This could result in a lot of requests, so you also have the option to provide
        a limit to only fetch a certain number of performance summaries.

        Args:
            performance_summary_id (str): The ID of the performance summary to retrieve.

        Returns:
            PerformanceSummary: The performance summary.

        Raises:
            ResourceNotFoundError: If the performance_summary_id is not in the list of performance summaries.
        """

        perf_summary = self.get_performance_summaries_dict(limit=limit).get(performance_summary_id)

        if perf_summary is None:
            raise exc.ResourceNotFoundError(f"Performance summary {performance_summary_id} not found")

        return perf_summary

    @functools.lru_cache(maxsize=1024)
    def _get_performancy_summary_detail(self, performance_summary_id: str) -> dict[str, Any]:
        """Get the details for a performance summary. Generally should not be called directly. This

        Args:
            performance_summary_id (str): The performance summary ID.

        Returns:
            dict[str, Any]: The performance summary details.

        Developer Notes:
            ---
            This is mostly here to cache the results of the raw method.
        """

        return self._get_performance_summary_raw(performance_summary_id)

    def get_hr_history(self) -> list[models.TelemetryHistoryItem]:
        """Get the heartrate history for the user.

        Returns a list of history items that contain the max heartrate, start/end bpm for each zone,
        the change from the previous, the change bucket, and the assigned at time.

        Returns:
            list[HistoryItem]: The heartrate history for the user.

        """
        resp = self._get_hr_history_raw()
        return [models.TelemetryHistoryItem(**item) for item in resp["history"]]

    def get_telemetry(self, performance_summary_id: str, max_data_points: int = 120) -> models.Telemetry:
        """Get the telemetry for a performance summary.

        This returns an object that contains the max heartrate, start/end bpm for each zone,
        and a list of telemetry items that contain the heartrate, splat points, calories, and timestamp.

        Args:
            performance_summary_id (str): The performance summary id.
            max_data_points (int): The max data points to use for the telemetry. Default is 120.

        Returns:
            TelemetryItem: The telemetry for the class history.
        """

        res = self._get_telemetry_raw(performance_summary_id, max_data_points)
        return models.Telemetry(**res)

    def get_sms_notification_settings(self) -> models.SmsNotificationSettings:
        """Get the member's SMS notification settings.

        Returns:
            SmsNotificationSettings: The member's SMS notification settings.
        """
        res = self._get_sms_notification_settings_raw()

        return models.SmsNotificationSettings(**res["data"])

    def update_sms_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.SmsNotificationSettings:
        """Update the member's SMS notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional SMS notifications.
            transactional_enabled (bool | None): Whether to enable transactional SMS notifications.

        Returns:
            SmsNotificationSettings: The updated SMS notification settings.

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

        current_settings = self.get_sms_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_sms_opt_in
        )
        transactional_enabled = (
            transactional_enabled if transactional_enabled is not None else current_settings.is_transactional_sms_opt_in
        )

        self._update_sms_notification_settings_raw(promotional_enabled, transactional_enabled)

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_sms_notification_settings()
        return new_settings

    def get_email_notification_settings(self) -> models.EmailNotificationSettings:
        """Get the member's email notification settings.

        Returns:
            EmailNotificationSettings: The member's email notification settings.
        """
        res = self._get_email_notification_settings_raw()

        return models.EmailNotificationSettings(**res["data"])

    def update_email_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.EmailNotificationSettings:
        """Update the member's email notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional email notifications.
            transactional_enabled (bool | None): Whether to enable transactional email notifications.

        Returns:
            EmailNotificationSettings: The updated email notification settings.
        """
        current_settings = self.get_email_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_email_opt_in
        )
        transactional_enabled = (
            transactional_enabled
            if transactional_enabled is not None
            else current_settings.is_transactional_email_opt_in
        )

        self._update_email_notification_settings_raw(promotional_enabled, transactional_enabled)

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_email_notification_settings()
        return new_settings

    def update_member_name(self, first_name: str | None = None, last_name: str | None = None) -> models.MemberDetail:
        """Update the member's name. Will return the original member details if no names are provided.

        Args:
            first_name (str | None): The first name to update to. Default is None.
            last_name (str | None): The last name to update to. Default is None.

        Returns:
            MemberDetail: The updated member details or the original member details if no changes were made.
        """

        if not first_name and not last_name:
            LOGGER.warning("No names provided, nothing to update.")
            return self.member

        first_name = first_name or self.member.first_name
        last_name = last_name or self.member.last_name

        if first_name == self.member.first_name and last_name == self.member.last_name:
            LOGGER.warning("No changes to names, nothing to update.")
            return self.member

        res = self._update_member_name_raw(first_name, last_name)

        return models.MemberDetail(**res["data"])

    def _rate_class(
        self,
        class_uuid: str,
        performance_summary_id: str,
        class_rating: Literal[0, 1, 2, 3],
        coach_rating: Literal[0, 1, 2, 3],
    ) -> models.PerformanceSummary:
        """Rate a class and coach. A simpler method is provided in `rate_class_from_performance_summary`.


        The class rating must be between 0 and 4.
        0 is the same as dismissing the prompt to rate the class/coach in the app.
        1 through 3 is a range from bad to good.

        Args:
            class_uuid (str): The class UUID.
            performance_summary_id (str): The performance summary ID.
            class_rating (int): The class rating. Must be 0, 1, 2, or 3.
            coach_rating (int): The coach rating. Must be 0, 1, 2, or 3.

        Returns:
            PerformanceSummary: The updated performance summary.
        """

        # com/orangetheoryfitness/fragment/rating/RateStatus.java

        # we convert these to the new values that the app uses
        # mainly because we don't want to cause any issues with the API and/or with OTF corporate
        # wondering where the old values are coming from

        COACH_RATING_MAP = {0: 0, 1: 16, 2: 17, 3: 18}
        CLASS_RATING_MAP = {0: 0, 1: 19, 2: 20, 3: 21}

        if class_rating not in CLASS_RATING_MAP:
            raise ValueError(f"Invalid class rating {class_rating}")

        if coach_rating not in COACH_RATING_MAP:
            raise ValueError(f"Invalid coach rating {coach_rating}")

        body_class_rating = CLASS_RATING_MAP[class_rating]
        body_coach_rating = COACH_RATING_MAP[coach_rating]

        try:
            self._rate_class_raw(class_uuid, performance_summary_id, body_class_rating, body_coach_rating)
        except exc.OtfRequestError as e:
            if e.response.status_code == 403:
                raise exc.AlreadyRatedError(f"Performance summary {performance_summary_id} is already rated.") from None
            raise

        # we have to clear the cache after rating a class, otherwise we will get back the same data
        # showing it not rated. that would be incorrect, confusing, and would cause errors if the user
        # then attempted to rate the class again.
        # we could attempt to only refresh the one record but with these endpoints that's not simple
        # NOTE: the individual perf summary endpoint does not have rating data, so it's cache is not cleared
        self.get_performance_summaries_dict.cache_clear()

        return self.get_performance_summary(performance_summary_id)

    def rate_class_from_performance_summary(
        self,
        perf_summary: models.PerformanceSummary,
        class_rating: Literal[0, 1, 2, 3],
        coach_rating: Literal[0, 1, 2, 3],
    ) -> models.PerformanceSummary:
        """Rate a class and coach. The class rating must be 0, 1, 2, or 3. 0 is the same as dismissing the prompt to
            rate the class/coach. 1 - 3 is a range from bad to good.

        Args:
            perf_summary (PerformanceSummary): The performance summary to rate.
            class_rating (int): The class rating. Must be 0, 1, 2, or 3.
            coach_rating (int): The coach rating. Must be 0, 1, 2, or 3.

        Returns:
            PerformanceSummary: The updated performance summary.

        Raises:
            AlreadyRatedError: If the performance summary is already rated.
            ClassNotRatableError: If the performance summary is not rateable.
            ValueError: If the performance summary does not have an associated class.
        """

        if perf_summary.is_rated:
            raise exc.AlreadyRatedError(f"Performance summary {perf_summary.performance_summary_id} is already rated.")

        if not perf_summary.ratable:
            raise exc.ClassNotRatableError(
                f"Performance summary {perf_summary.performance_summary_id} is not rateable."
            )

        if not perf_summary.otf_class or not perf_summary.otf_class.class_uuid:
            raise ValueError(
                f"Performance summary {perf_summary.performance_summary_id} does not have an associated class."
            )

        return self._rate_class(
            perf_summary.otf_class.class_uuid, perf_summary.performance_summary_id, class_rating, coach_rating
        )

    # the below do not return any data for me, so I can't test them

    def _get_member_services(self, active_only: bool = True) -> Any:
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's services.
        """
        data = self._get_member_services_raw(active_only)
        return data

    def _get_aspire_data(self, datetime: str | None = None, unit: str | None = None) -> Any:
        """Get data from the member's aspire wearable.

        Note: I don't have an aspire wearable, so I can't test this.

        Args:
            datetime (str | None): The date and time to get data for. Default is None.
            unit (str | None): The measurement unit. Default is None.

        Returns:
            Any: The member's aspire data.
        """
        data = self._get_aspire_data_raw(datetime, unit)
        return data
