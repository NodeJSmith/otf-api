import atexit
import contextlib
import functools
from datetime import date, datetime, timedelta
from json import JSONDecodeError
from logging import getLogger
from typing import Any, Literal

import attrs
import httpx
from yarl import URL

from otf_api import exceptions as exc
from otf_api import filters, models
from otf_api.auth import OtfUser
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
            LOGGER.exception(f"Error making request: {e}")
            LOGGER.exception(f"Response: {response.text}")
            raise exc.OtfRequestError("Error making request", response=response, request=request)
        except Exception as e:
            LOGGER.exception(f"Error making request: {e}")
            raise

        if not response.text:
            return None

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
            raise exc.OtfRequestError("Error making request", response=response, request=request)

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

        classes_resp = self._classes_request("GET", "/v1/classes", params={"studio_ids": studio_uuids})

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

        data = self._default_request("GET", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}")
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
        status: models.BookingStatus | None = None,
        exclude_cancelled: bool = True,
        exclude_checkedin: bool = True,
    ) -> list[models.Booking]:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | None): The status of the bookings to get. Default is None, which includes\
            all statuses. Only a single status can be provided.
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

        Developer Notes:
            ---
            Looking at the code in the app, it appears that this endpoint accepts multiple statuses. Indeed,
            it does not throw an error if you include a list of statuses. However, only the last status in the list is
            used. I'm not sure if this is a bug or if the API is supposed to work this way.
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

        status_value = status.value if status else None

        params = {"startDate": start_date, "endDate": end_date, "statuses": status_value}

        resp = self._default_request("GET", f"/member/members/{self.member_uuid}/bookings", params=params)["data"]

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

    def _get_bookings_old(self, status: models.BookingStatus | None = None) -> list[models.Booking]:
        """Get the member's bookings.

        Args:
            status (BookingStatus | None): The status of the bookings to get. Default is None, which includes
            all statuses. Only a single status can be provided.

        Returns:
            list[Booking]: The member's bookings.

        Raises:
            ValueError: If an unaccepted status is provided.

        Notes:
        ---
            This one is called with the param named 'status'. Dates cannot be provided, because if the endpoint
            receives a date, it will return as if the param name was 'statuses'.

            Note: This seems to only work for Cancelled, Booked, CheckedIn, and Waitlisted statuses. If you provide
            a different status, it will return all bookings, not filtered by status. The results in this scenario do
            not line up with the `get_bookings` with no status provided, as that returns fewer records. Likely the
            filtered dates are different on the backend.

            My guess: the endpoint called with dates and 'statuses' is a "v2" kind of thing, where they upgraded without
            changing the version of the api. Calling it with no dates and a singular (limited) status is probably v1.

            I'm leaving this in here for reference, but marking it private. I just don't want to have to puzzle over
            this again if I remove it and forget about it.

        """

        if status and status not in [
            models.BookingStatus.Cancelled,
            models.BookingStatus.Booked,
            models.BookingStatus.CheckedIn,
            models.BookingStatus.Waitlisted,
        ]:
            raise ValueError(
                "Invalid status provided. Only Cancelled, Booked, CheckedIn, Waitlisted, and None are supported."
            )

        status_value = status.value if status else None

        res = self._default_request(
            "GET", f"/member/members/{self.member_uuid}/bookings", params={"status": status_value}
        )

        return [models.Booking(**b) for b in res["data"]]

    def get_member_detail(self) -> models.MemberDetail:
        """Get the member details.

        Returns:
            MemberDetail: The member details.
        """

        params = {"include": "memberAddresses,memberClassSummary"}

        resp = self._default_request("GET", f"/member/members/{self.member_uuid}", params=params)
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

        data = self._default_request("GET", f"/member/members/{self.member_uuid}/memberships")
        return models.MemberMembership(**data["data"])

    def get_member_purchases(self) -> list[models.MemberPurchase]:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            list[MemberPurchase]: The member's purchases.
        """
        data = self._default_request("GET", f"/member/members/{self.member_uuid}/purchases")

        purchases = data["data"]

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

        data = self._default_request("GET", f"/performance/v2/{self.member_uuid}/over-time/{select_time}")

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
        data = self._default_request("GET", f"/member/members/{self.member_uuid}/out-of-studio-workout")

        return [models.OutOfStudioWorkoutHistory(**workout) for workout in data["data"]]

    def get_favorite_studios(self) -> list[models.StudioDetail]:
        """Get the member's favorite studios.

        Returns:
            list[StudioDetail]: The member's favorite studios.
        """
        data = self._default_request("GET", f"/member/members/{self.member_uuid}/favorite-studios")
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

        body = {"studioUUIds": studio_uuids}
        resp = self._default_request("POST", "/mobile/v1/members/favorite-studios", json=body)

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

        body = {"studioUUIds": studio_uuids}
        self._default_request("DELETE", "/mobile/v1/members/favorite-studios", json=body)

    def get_studio_services(self, studio_uuid: str | None = None) -> list[models.StudioService]:
        """Get the services available at a specific studio. If no studio UUID is provided, the member's home studio
        will be used.

        Args:
            studio_uuid (str, optional): The studio UUID to get services for.

        Returns:
            list[StudioService]: The services available at the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid
        data = self._default_request("GET", f"/member/studios/{studio_uuid}/services")

        for d in data["data"]:
            d["studio"] = self.get_studio_detail(studio_uuid)

        return [models.StudioService(**d) for d in data["data"]]

    @functools.cache
    def get_studio_detail(self, studio_uuid: str | None = None) -> models.StudioDetail:
        """Get detailed information about a specific studio. If no studio UUID is provided, it will default to the
        user's home studio.

        Args:
            studio_uuid (str, optional): The studio UUID to get detailed information about.

        Returns:
            StudioDetail: Detailed information about the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid

        path = f"/mobile/v1/studios/{studio_uuid}"

        res = self._default_request("GET", path)

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
        path = "/mobile/v1/studios"

        distance = min(distance, 250)  # max distance is 250 miles

        params = {"latitude": latitude, "longitude": longitude, "distance": distance, "pageIndex": 1, "pageSize": 100}

        LOGGER.debug("Starting studio search", extra={"params": params})

        all_results: dict[str, dict[str, Any]] = {}

        while True:
            res = self._default_request("GET", path, params=params)
            studios = res["data"].get("studios", [])
            total_count = res["data"].get("pagination", {}).get("totalCount", 0)

            all_results.update({studio["studioUUId"]: studio for studio in studios})
            if len(all_results) >= total_count or not studios:
                break

            params["pageIndex"] += 1

        LOGGER.info("Studio search completed, fetched %d of %d studios", len(all_results), total_count, stacklevel=2)

        return [models.StudioDetail(**studio) for studio in all_results.values()]

    def get_body_composition_list(self) -> list[models.BodyCompositionData]:
        """Get the member's body composition list.

        Returns:
            list[BodyCompositionData]: The member's body composition list.
        """
        data = self._default_request("GET", f"/member/members/{self.user.cognito_id}/body-composition")
        return [models.BodyCompositionData(**item) for item in data["data"]]

    def get_challenge_tracker(self) -> models.ChallengeTracker:
        """Get the member's challenge tracker content.

        Returns:
            ChallengeTracker: The member's challenge tracker content.
        """
        data = self._default_request("GET", f"/challenges/v3.1/member/{self.member_uuid}")
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
        params = {
            "equipmentId": int(equipment_id),
            "challengeTypeId": int(challenge_category_id),
            "challengeSubTypeId": challenge_subcategory_id,
        }

        data = self._default_request("GET", f"/challenges/v3/member/{self.member_uuid}/benchmarks", params=params)
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

        data = self._default_request(
            "GET",
            f"/challenges/v1/member/{self.member_uuid}/participation",
            params={"challengeTypeId": int(challenge_category_id)},
        )

        if len(data["Dto"]) > 1:
            LOGGER.warning("Multiple challenge participations found, returning the first one.")

        if len(data["Dto"]) == 0:
            raise exc.ResourceNotFoundError(f"Challenge {challenge_category_id} not found")

        return models.FitnessBenchmark(**data["Dto"][0])

    def get_performance_summaries(self, limit: int = 5) -> list[models.PerformanceSummaryEntry]:
        """Get a list of performance summaries for the authenticated user.

        Args:
            limit (int): The maximum number of performance summaries to return. Defaults to 5.
            only_include_rateable (bool): Whether to only include rateable performance summaries. Defaults to True.

        Returns:
            list[PerformanceSummaryEntry]: A list of performance summaries.

        Developer Notes:
            ---
            In the app, this is referred to as 'getInStudioWorkoutHistory'.

        """

        res = self._performance_summary_request("GET", "/v1/performance-summaries", params={"limit": limit})
        entries = [models.PerformanceSummaryEntry(**item) for item in res["items"]]

        return entries

    def get_performance_summary(self, performance_summary_id: str) -> models.PerformanceSummaryDetail:
        """Get a detailed performance summary for a given workout.

        Args:
            performance_summary_id (str): The ID of the performance summary to retrieve.

        Returns:
            PerformanceSummaryDetail: A detailed performance summary.
        """

        path = f"/v1/performance-summaries/{performance_summary_id}"
        res = self._performance_summary_request("GET", path)
        if res is None:
            raise exc.ResourceNotFoundError(f"Performance summary {performance_summary_id} not found")

        return models.PerformanceSummaryDetail(**res)

    def get_hr_history(self) -> list[models.TelemetryHistoryItem]:
        """Get the heartrate history for the user.

        Returns a list of history items that contain the max heartrate, start/end bpm for each zone,
        the change from the previous, the change bucket, and the assigned at time.

        Returns:
            list[HistoryItem]: The heartrate history for the user.

        """
        path = "/v1/physVars/maxHr/history"

        params = {"memberUuid": self.member_uuid}
        resp = self._telemetry_request("GET", path, params=params)
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
        path = "/v1/performance/summary"

        params = {"classHistoryUuid": performance_summary_id, "maxDataPoints": max_data_points}
        res = self._telemetry_request("GET", path, params=params)
        return models.Telemetry(**res)

    def get_sms_notification_settings(self):
        res = self._default_request("GET", url="/sms/v1/preferences", params={"phoneNumber": self.member.phone_number})

        return res["data"]

    def update_sms_notification_settings(self, promotional_enabled: bool, transactional_enabled: bool):
        url = "/sms/v1/preferences"

        body = {
            "promosms": promotional_enabled,
            "source": "OTF",
            "transactionalsms": transactional_enabled,
            "phoneNumber": self.member.phone_number,
        }

        res = self._default_request("POST", url, json=body)

        return res["data"]

    def update_email_notification_settings(self, promotional_enabled: bool, transactional_enabled: bool):
        body = {
            "promotionalEmail": promotional_enabled,
            "source": "OTF",
            "transactionalEmail": transactional_enabled,
            "email": self.member.email,
        }

        res = self._default_request("POST", "/otfmailing/v2/preferences", json=body)

        return res["data"]

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

        path = f"/member/members/{self.member_uuid}"
        body = {"firstName": first_name, "lastName": last_name}

        res = self._default_request("PUT", path, json=body)

        return models.MemberDetail(**res["data"])

    # the below do not return any data for me, so I can't test them

    def _get_member_services(self, active_only: bool = True) -> Any:
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's services.
        """
        active_only_str = "true" if active_only else "false"
        data = self._default_request(
            "GET", f"/member/members/{self.member_uuid}/services", params={"activeOnly": active_only_str}
        )
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
        params = {"datetime": datetime, "unit": unit}

        data = self._default_request("GET", f"/member/wearables/{self.member_uuid}/wearable-daily", params=params)
        return data
