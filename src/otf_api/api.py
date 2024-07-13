import asyncio
import contextlib
import json
import signal
import typing
from datetime import date, datetime
from math import ceil
from typing import Any

import aiohttp
from loguru import logger
from yarl import URL

from otf_api.auth import OtfUser
from otf_api.models.responses.body_composition_list import BodyCompositionList
from otf_api.models.responses.book_class import BookClass
from otf_api.models.responses.cancel_booking import CancelBooking
from otf_api.models.responses.classes import ClassType, DoW, OtfClassList
from otf_api.models.responses.favorite_studios import FavoriteStudioList
from otf_api.models.responses.lifetime_stats import StatsResponse, StatsTime
from otf_api.models.responses.performance_summary_detail import PerformanceSummaryDetail
from otf_api.models.responses.performance_summary_list import PerformanceSummaryList
from otf_api.models.responses.studio_detail import Pagination, StudioDetail, StudioDetailList
from otf_api.models.responses.telemetry import Telemetry
from otf_api.models.responses.telemetry_hr_history import TelemetryHrHistory
from otf_api.models.responses.telemetry_max_hr import TelemetryMaxHr

from .models import (
    BookingList,
    BookingStatus,
    ChallengeTrackerContent,
    ChallengeTrackerDetailList,
    ChallengeType,
    EquipmentType,
    LatestAgreement,
    MemberDetail,
    MemberMembership,
    MemberPurchaseList,
    OutOfStudioWorkoutHistoryList,
    StudioServiceList,
    TotalClasses,
    WorkoutList,
)


class AlreadyBookedError(Exception):
    pass


if typing.TYPE_CHECKING:
    from loguru import Logger


API_BASE_URL = "api.orangetheory.co"
API_IO_BASE_URL = "api.orangetheory.io"
API_TELEMETRY_BASE_URL = "api.yuzu.orangetheory.com"
REQUEST_HEADERS = {"Authorization": None, "Content-Type": "application/json", "Accept": "application/json"}


class Otf:
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
    user: OtfUser
    session: aiohttp.ClientSession

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        id_token: str | None = None,
    ):
        self.member: MemberDetail
        self.home_studio: StudioDetail

        # Handle shutdown
        try:
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
        except Exception:
            pass

        if username and password:
            self.user = OtfUser.login(username, password)
        elif access_token and id_token:
            self.user = OtfUser.from_token(access_token, id_token)
        else:
            raise ValueError("Either username and password or access_token and id_token must be provided.")

        headers = {
            "Authorization": f"Bearer {self.user.cognito.id_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session = aiohttp.ClientSession(headers=headers)

        # simplify access to member_id and member_uuid
        self._member_id = self.user.member_id
        self._member_uuid = self.user.member_uuid
        self._perf_api_headers = {
            "koji-member-id": self._member_id,
            "koji-member-email": self.user.id_claims_data.email,
        }

        self.start_background_refresh()

    @classmethod
    async def create(
        cls,
        username: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        id_token: str | None = None,
    ) -> "Otf":
        """Create a new API instance. Accepts either a username and password or an access token and id token.

        Args:
            username (str, None): The username of the user. Default is None.
            password (str, None): The password of the user. Default is None.
            access_token (str, None): The access token. Default is None.
            id_token (str, None): The id token. Default is None.

        Returns:
            Api: The API instance.
        """

        self = cls(username=username, password=password, access_token=access_token, id_token=id_token)
        self.member = await self.get_member_detail()
        self.home_studio = await self.get_studio_detail(self.member.home_studio.studio_uuid)
        return self

    @classmethod
    async def create_with_username(cls, username: str, password: str) -> "Otf":
        """Create a new API instance. The username and password are required arguments because even though
        we cache the token, they expire so quickly that we usually end up needing to re-authenticate.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.
        """
        self = cls(username, password)
        self.member = await self.get_member_detail()
        self.home_studio = await self.get_studio_detail(self.member.home_studio.studio_uuid)
        return self

    @classmethod
    async def create_with_token(cls, access_token: str, id_token: str) -> "Otf":
        """Create a new API instance. The username and password are required arguments because even though
        we cache the token, they expire so quickly that we usually end up needing to re-authenticate.

        Args:
            access_token (str): The access token.
            id_token (str): The id token.
        """
        self = cls(access_token=access_token, id_token=id_token)
        self.member = await self.get_member_detail()
        self.home_studio = await self.get_studio_detail(self.member.home_studio.studio_uuid)
        return self

    def start_background_refresh(self) -> None:
        """Start the background task for refreshing the token."""
        logger.debug("Starting background task for refreshing token.")
        self._refresh_task = asyncio.create_task(self._run_refresh_on_loop())

    async def _run_refresh_on_loop(self) -> None:
        """Run the refresh token method on a loop to keep the token fresh."""
        try:
            while True:
                await asyncio.sleep(300)
                self.user = self.user.refresh_token()
        except asyncio.CancelledError:
            pass

    def shutdown(self, *_args) -> None:
        """Shutdown the background task and event loop."""
        if hasattr(self, "_refresh_task") and self._refresh_task:
            self._refresh_task.cancel()

    def __del__(self) -> None:
        if not hasattr(self, "session"):
            return
        try:
            asyncio.create_task(self._close_session())  # noqa
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._close_session())

    async def _close_session(self) -> None:
        if not self.session.closed:
            await self.session.close()

    async def _do(
        self,
        method: str,
        base_url: str,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Perform an API request."""

        params = params or {}
        params = {k: v for k, v in params.items() if v is not None}

        full_url = str(URL.build(scheme="https", host=base_url, path=url))

        logger.debug(f"Making {method!r} request to {full_url}, params: {params}")

        text = None
        async with self.session.request(method, full_url, headers=headers, params=params, **kwargs) as response:
            with contextlib.suppress(Exception):
                text = await response.text()

            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError as e:
                logger.exception(f"Error making request: {e}")
                logger.exception(f"Response: {text}")
                # raise
            except Exception as e:
                logger.exception(f"Error making request: {e}")
                # raise

            return await response.json()

    async def _classes_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the classes API."""
        return await self._do(method, API_IO_BASE_URL, url, params)

    async def _default_request(self, method: str, url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """Perform an API request to the default API."""
        return await self._do(method, API_BASE_URL, url, params, **kwargs)

    async def _telemetry_request(self, method: str, url: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an API request to the Telemetry API."""
        return await self._do(method, API_TELEMETRY_BASE_URL, url, params)

    async def _performance_summary_request(
        self, method: str, url: str, headers: dict[str, str], params: dict[str, Any] | None = None
    ) -> Any:
        """Perform an API request to the performance summary API."""
        return await self._do(method, API_IO_BASE_URL, url, params, headers)

    async def get_workouts(self) -> WorkoutList:
        """Get the list of workouts from OT Live.

        Returns:
            WorkoutList: The list of workouts.

        Info:
            ---
            This returns data from the same api the [OT Live website](https://otlive.orangetheory.com/) uses.
            It is quite a bit of data, and all workouts going back to ~2019. The data includes the class history
            UUID, which can be used to get telemetry data for a specific workout.
        """

        res = await self._default_request("GET", "/virtual-class/in-studio-workouts")

        return WorkoutList(workouts=res["data"])

    async def get_total_classes(self) -> TotalClasses:
        """Get the member's total classes. This is a simple object reflecting the total number of classes attended,
        both in-studio and OT Live.

        Returns:
            TotalClasses: The member's total classes.
        """
        data = await self._default_request("GET", "/mobile/v1/members/classes/summary")
        return TotalClasses(**data["data"])

    async def get_classes(
        self,
        studio_uuids: list[str] | None = None,
        include_home_studio: bool = True,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        class_type: ClassType | list[ClassType] | None = None,
        exclude_cancelled: bool = False,
        day_of_week: list[DoW] | None = None,
        start_time: list[str] | None = None,
    ) -> OtfClassList:
        """Get the classes for the user.

        Returns a list of classes that are available for the user, based on the studio UUIDs provided. If no studio
        UUIDs are provided, it will default to the user's home studio.

        Args:
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will\
            default to the user's home studio only.
            include_home_studio (bool): Whether to include the home studio in the classes. Default is True.
            start_date (str | None): The start date to get classes for, in the format "YYYY-MM-DD". Default is None.
            end_date (str | None): The end date to get classes for, in the format "YYYY-MM-DD". Default is None.
            limit (int | None): Limit the number of classes returned. Default is None.
            class_type (ClassType | list[ClassType] | None): The class type to filter by. Default is None. Multiple\
            class types can be provided, if there are multiple there will be a call per class type.
            exclude_cancelled (bool): Whether to exclude cancelled classes. Default is False.
            day_of_week (list[DoW] | None): The days of the week to filter by. Default is None.
            start_time (list[str] | None): The start time to filter by. Default is None.

        Returns:
            OtfClassList: The classes for the user.
        """

        if not studio_uuids:
            studio_uuids = [self.home_studio.studio_uuid]
        elif include_home_studio and self.home_studio.studio_uuid not in studio_uuids:
            studio_uuids.append(self.home_studio.studio_uuid)

        path = "/v1/classes"

        params = {"studio_ids": studio_uuids}

        classes_resp = await self._classes_request("GET", path, params=params)
        classes_list = OtfClassList(classes=classes_resp["items"])

        if start_date:
            start_dtme = datetime.strptime(start_date, "%Y-%m-%d")  # noqa
            classes_list.classes = [c for c in classes_list.classes if c.starts_at_local >= start_dtme]

        if end_date:
            end_dtme = datetime.strptime(end_date, "%Y-%m-%d")  # noqa
            classes_list.classes = [c for c in classes_list.classes if c.ends_at_local <= end_dtme]

        if limit:
            classes_list.classes = classes_list.classes[:limit]

        if class_type and isinstance(class_type, str):
            class_type = [class_type]

        if day_of_week and not isinstance(day_of_week, list):
            day_of_week = [day_of_week]

        if start_time and not isinstance(start_time, list):
            start_time = [start_time]

        if class_type:
            classes_list.classes = [c for c in classes_list.classes if c.class_type in class_type]

        if exclude_cancelled:
            classes_list.classes = [c for c in classes_list.classes if not c.canceled]

        for otf_class in classes_list.classes:
            otf_class.is_home_studio = otf_class.studio.id == self.home_studio.studio_uuid

        if day_of_week:
            classes_list.classes = [c for c in classes_list.classes if c.day_of_week_enum in day_of_week]

        if start_time:
            classes_list.classes = [
                c for c in classes_list.classes if any(c.time.strip().startswith(t) for t in start_time)
            ]

        classes_list.classes = list(filter(lambda c: not c.canceled, classes_list.classes))

        booking_resp = await self.get_bookings(start_date, end_date, status=BookingStatus.Booked)
        booked_classes = {b.otf_class.class_uuid for b in booking_resp.bookings}

        for otf_class in classes_list.classes:
            otf_class.is_booked = otf_class.ot_class_uuid in booked_classes

        return classes_list

    async def book_class(self, class_uuid: str) -> BookClass | typing.Any:
        """Book a class by class_uuid.

        Args:
            class_uuid (str): The class UUID to book.

        Returns:
            None: The response is empty.
        """

        bookings = await self.get_bookings()

        for booking in bookings.bookings:
            if booking.otf_class.class_uuid == class_uuid:
                raise AlreadyBookedError(f"Class {class_uuid} is already booked.")

        body = {"classUUId": class_uuid, "confirmed": False, "waitlist": False}

        resp = await self._default_request("PUT", f"/member/members/{self._member_id}/bookings", json=body)

        if resp["code"] == "ERROR":
            if resp["data"]["errorCode"] == "603":
                raise AlreadyBookedError(f"Class {class_uuid} is already booked.")
            raise Exception(f"Error booking class {class_uuid}: {json.dumps(resp)}")

        data = BookClass(**resp["data"])
        return data

    async def cancel_booking(self, booking_uuid: str) -> CancelBooking:
        """Cancel a class by booking_uuid.

        Args:
            booking_uuid (str): The booking UUID to cancel.

        Returns:
            None: The response is empty.
        """

        params = {"confirmed": "true"}
        resp = await self._default_request(
            "DELETE", f"/member/members/{self._member_id}/bookings/{booking_uuid}", params=params
        )
        return CancelBooking(**resp["data"])

    async def get_bookings(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        status: BookingStatus | None = None,
        limit: int | None = None,
        exclude_cancelled: bool = True,
        exclude_checkedin: bool = True,
    ) -> BookingList:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | None): The status of the bookings to get. Default is None, which includes\
            all statuses. Only a single status can be provided.
            limit (int | None): The maximum number of bookings to return. Default is None, which returns all\
            bookings.
            exclude_cancelled (bool): Whether to exclude cancelled bookings. Default is True.
            exclude_checkedin (bool): Whether to exclude checked-in bookings. Default is True.

        Returns:
            BookingList: The member's bookings.

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

        if exclude_cancelled and status == BookingStatus.Cancelled:
            logger.warning(
                "Cannot exclude cancelled bookings when status is Cancelled. Setting exclude_cancelled to False."
            )
            exclude_cancelled = False

        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        status_value = status.value if status else None

        params = {"startDate": start_date, "endDate": end_date, "statuses": status_value}

        res = await self._default_request("GET", f"/member/members/{self._member_id}/bookings", params=params)

        bookings = res["data"][:limit] if limit else res["data"]

        data = BookingList(bookings=bookings)
        data.bookings = sorted(data.bookings, key=lambda x: x.otf_class.starts_at_local)

        for booking in data.bookings:
            if not booking.otf_class:
                continue
            if booking.otf_class.studio.studio_uuid == self.home_studio.studio_uuid:
                booking.is_home_studio = True
            else:
                booking.is_home_studio = False

        if exclude_cancelled:
            data.bookings = [b for b in data.bookings if b.status != BookingStatus.Cancelled]

        if exclude_checkedin:
            data.bookings = [b for b in data.bookings if b.status != BookingStatus.CheckedIn]

        return data

    async def _get_bookings_old(self, status: BookingStatus | None = None) -> BookingList:
        """Get the member's bookings.

        Args:
            status (BookingStatus | None): The status of the bookings to get. Default is None, which includes
            all statuses. Only a single status can be provided.

        Returns:
            BookingList: The member's bookings.

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
            BookingStatus.Cancelled,
            BookingStatus.Booked,
            BookingStatus.CheckedIn,
            BookingStatus.Waitlisted,
        ]:
            raise ValueError(
                "Invalid status provided. Only Cancelled, Booked, CheckedIn, Waitlisted, and None are supported."
            )

        status_value = status.value if status else None

        params = {"status": status_value}

        res = await self._default_request("GET", f"/member/members/{self._member_id}/bookings", params=params)

        return BookingList(bookings=res["data"])

    async def get_challenge_tracker_content(self) -> ChallengeTrackerContent:
        """Get the member's challenge tracker content.

        Returns:
            ChallengeTrackerContent: The member's challenge tracker content.
        """
        data = await self._default_request("GET", f"/challenges/v3.1/member/{self._member_id}")
        return ChallengeTrackerContent(**data["Dto"])

    async def get_challenge_tracker_detail(
        self, equipment_id: EquipmentType, challenge_type_id: ChallengeType, challenge_sub_type_id: int = 0
    ) -> ChallengeTrackerDetailList:
        """Get the member's challenge tracker details.

        Args:
            equipment_id (EquipmentType): The equipment ID.
            challenge_type_id (ChallengeType): The challenge type ID.
            challenge_sub_type_id (int): The challenge sub type ID. Default is 0.

        Returns:
            ChallengeTrackerDetailList: The member's challenge tracker details.

        Notes:
            ---
            I'm not sure what the challenge_sub_type_id is supposed to be, so it defaults to 0.

        """
        params = {
            "equipmentId": equipment_id.value,
            "challengeTypeId": challenge_type_id.value,
            "challengeSubTypeId": challenge_sub_type_id,
        }

        data = await self._default_request("GET", f"/challenges/v3/member/{self._member_id}/benchmarks", params=params)

        return ChallengeTrackerDetailList(details=data["Dto"])

    async def get_challenge_tracker_participation(self, challenge_type_id: ChallengeType) -> typing.Any:
        """Get the member's participation in a challenge.

        Args:
            challenge_type_id (ChallengeType): The challenge type ID.

        Returns:
            Any: The member's participation in the challenge.

        Notes:
            ---
            I've never gotten this to return anything other than invalid response. I'm not sure if it's a bug
            in my code or the API.

        """
        params = {"challengeTypeId": challenge_type_id.value}

        data = await self._default_request(
            "GET", f"/challenges/v1/member/{self._member_id}/participation", params=params
        )
        return data

    async def get_member_detail(
        self, include_addresses: bool = True, include_class_summary: bool = True, include_credit_card: bool = False
    ) -> MemberDetail:
        """Get the member details.

        Args:
            include_addresses (bool): Whether to include the member's addresses in the response.
            include_class_summary (bool): Whether to include the member's class summary in the response.
            include_credit_card (bool): Whether to include the member's credit card information in the response.

        Returns:
            MemberDetail: The member details.


        Notes:
            ---
            The include_addresses, include_class_summary, and include_credit_card parameters are optional and determine
            what additional information is included in the response. By default, all additional information is included,
            with the exception of the credit card information.

            The base member details include the last four of a credit card regardless of the include_credit_card,
            although this is not always the same details as what is in the member_credit_card field. There doesn't seem
            to be a way to exclude this information, and I do not know which is which or why they differ.
        """

        include: list[str] = []
        if include_addresses:
            include.append("memberAddresses")

        if include_class_summary:
            include.append("memberClassSummary")

        if include_credit_card:
            include.append("memberCreditCard")

        params = {"include": ",".join(include)} if include else None

        data = await self._default_request("GET", f"/member/members/{self._member_id}", params=params)
        return MemberDetail(**data["data"])

    async def get_member_membership(self) -> MemberMembership:
        """Get the member's membership details.

        Returns:
            MemberMembership: The member's membership details.
        """

        data = await self._default_request("GET", f"/member/members/{self._member_id}/memberships")
        return MemberMembership(**data["data"])

    async def get_member_purchases(self) -> MemberPurchaseList:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            MemberPurchaseList: The member's purchases.
        """
        data = await self._default_request("GET", f"/member/members/{self._member_id}/purchases")
        return MemberPurchaseList(data=data["data"])

    async def get_member_lifetime_stats(self, select_time: StatsTime = StatsTime.AllTime) -> StatsResponse:
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

        data = await self._default_request("GET", f"/performance/v2/{self._member_id}/over-time/{select_time.value}")

        stats = StatsResponse(**data["data"])
        return stats

    async def get_out_of_studio_workout_history(self) -> OutOfStudioWorkoutHistoryList:
        """Get the member's out of studio workout history.

        Returns:
            OutOfStudioWorkoutHistoryList: The member's out of studio workout history.
        """
        data = await self._default_request("GET", f"/member/members/{self._member_id}/out-of-studio-workout")

        return OutOfStudioWorkoutHistoryList(data=data["data"])

    async def get_favorite_studios(self) -> FavoriteStudioList:
        """Get the member's favorite studios.

        Returns:
            FavoriteStudioList: The member's favorite studios.
        """
        data = await self._default_request("GET", f"/member/members/{self._member_id}/favorite-studios")

        return FavoriteStudioList(studios=data["data"])

    async def get_latest_agreement(self) -> LatestAgreement:
        """Get the latest agreement for the member.

        Returns:
            LatestAgreement: The agreement.

        Notes:
        ---
            In this context, "latest" means the most recent agreement with a specific ID, not the most recent agreement
            in general. The agreement ID is hardcoded in the endpoint, so it will always return the same agreement.
        """
        data = await self._default_request("GET", "/member/agreements/9d98fb27-0f00-4598-ad08-5b1655a59af6")
        return LatestAgreement(**data["data"])

    async def get_studio_services(self, studio_uuid: str | None = None) -> StudioServiceList:
        """Get the services available at a specific studio. If no studio UUID is provided, the member's home studio
        will be used.

        Args:
            studio_uuid (str): The studio UUID to get services for. Default is None, which will use the member's home\
            studio.

        Returns:
            StudioServiceList: The services available at the studio.
        """
        studio_uuid = studio_uuid or self.home_studio.studio_uuid
        data = await self._default_request("GET", f"/member/studios/{studio_uuid}/services")
        return StudioServiceList(data=data["data"])

    async def get_performance_summaries(self, limit: int = 30) -> PerformanceSummaryList:
        """Get a list of performance summaries for the authenticated user.

        Args:
            limit (int): The maximum number of performance summaries to return. Defaults to 30.

        Returns:
            PerformanceSummaryList: A list of performance summaries.

        Developer Notes:
            ---
            In the app, this is referred to as 'getInStudioWorkoutHistory'.

        """

        path = "/v1/performance-summaries"
        params = {"limit": limit}
        res = await self._performance_summary_request("GET", path, headers=self._perf_api_headers, params=params)
        retval = PerformanceSummaryList(summaries=res["items"])
        return retval

    async def get_performance_summary(self, performance_summary_id: str) -> PerformanceSummaryDetail:
        """Get a detailed performance summary for a given workout.

        Args:
            performance_summary_id (str): The ID of the performance summary to retrieve.

        Returns:
            PerformanceSummaryDetail: A detailed performance summary.
        """

        path = f"/v1/performance-summaries/{performance_summary_id}"
        res = await self._performance_summary_request("GET", path, headers=self._perf_api_headers)
        retval = PerformanceSummaryDetail(**res)
        return retval

    async def get_studio_detail(self, studio_uuid: str | None = None) -> StudioDetail:
        """Get detailed information about a specific studio. If no studio UUID is provided, it will default to the
        user's home studio.

        Args:
            studio_uuid (str): Studio UUID to get details for. Defaults to None, which will default to the user's home\
            studio.

        Returns:
            StudioDetail: Detailed information about the studio.
        """
        studio_uuid = studio_uuid or self.home_studio.studio_uuid

        path = f"/mobile/v1/studios/{studio_uuid}"
        params = {"include": "locations"}

        res = await self._default_request("GET", path, params=params)
        return StudioDetail(**res["data"])

    async def search_studios_by_geo(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        distance: float = 50,
        page_index: int = 1,
        page_size: int = 50,
    ) -> StudioDetailList:
        """Search for studios by geographic location.

        Args:
            latitude (float, optional): Latitude of the location to search around, if None uses home studio latitude.
            longitude (float, optional): Longitude of the location to search around, if None uses home studio longitude.
            distance (float, optional): Distance in miles to search around the location. Defaults to 50.
            page_index (int, optional): Page index to start at. Defaults to 1.
            page_size (int, optional): Number of results per page. Defaults to 50.

        Returns:
            StudioDetailList: List of studios that match the search criteria.

        Notes:
            ---
            There does not seem to be a limit to the number of results that can be requested total or per page, the
            library enforces a limit of 50 results per page to avoid potential rate limiting issues.

        """
        path = "/mobile/v1/studios"

        latitude = latitude or self.home_studio.studio_location.latitude
        longitude = longitude or self.home_studio.studio_location.longitude

        if page_size > 50:
            self.logger.warning("The API does not support more than 50 results per page, limiting to 50.")
            page_size = 50

        if page_index < 1:
            self.logger.warning("Page index must be greater than 0, setting to 1.")
            page_index = 1

        params = {
            "pageIndex": page_index,
            "pageSize": page_size,
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance,
        }

        all_results: list[StudioDetail] = []

        while True:
            res = await self._default_request("GET", path, params=params)
            pagination = Pagination(**res["data"].pop("pagination"))
            all_results.extend([StudioDetail(**studio) for studio in res["data"]["studios"]])

            if len(all_results) == pagination.total_count:
                break

            params["pageIndex"] += 1

        return StudioDetailList(studios=all_results)

    async def get_hr_history(self) -> TelemetryHrHistory:
        """Get the heartrate history for the user.

        Returns a list of history items that contain the max heartrate, start/end bpm for each zone,
        the change from the previous, the change bucket, and the assigned at time.

        Returns:
            TelemetryHrHistory: The heartrate history for the user.

        """
        path = "/v1/physVars/maxHr/history"

        params = {"memberUuid": self._member_id}
        res = await self._telemetry_request("GET", path, params=params)
        return TelemetryHrHistory(**res)

    async def get_max_hr(self) -> TelemetryMaxHr:
        """Get the max heartrate for the user.

        Returns a simple object that has the member_uuid and the max_hr.

        Returns:
            TelemetryMaxHr: The max heartrate for the user.
        """
        path = "/v1/physVars/maxHr"

        params = {"memberUuid": self._member_id}

        res = await self._telemetry_request("GET", path, params=params)
        return TelemetryMaxHr(**res)

    async def get_telemetry(self, class_history_uuid: str, max_data_points: int = 0) -> Telemetry:
        """Get the telemetry for a class history.

        This returns an object that contains the max heartrate, start/end bpm for each zone,
        and a list of telemetry items that contain the heartrate, splat points, calories, and timestamp.

        Args:
            class_history_uuid (str): The class history UUID.
            max_data_points (int): The max data points to use for the telemetry. Default is 0, which will attempt to\
            get the max data points from the workout. If the workout is not found, it will default to 120 data points.

        Returns:
            TelemetryItem: The telemetry for the class history.

        """
        path = "/v1/performance/summary"

        max_data_points = max_data_points or await self._get_max_data_points(class_history_uuid)

        params = {"classHistoryUuid": class_history_uuid, "maxDataPoints": max_data_points}
        res = await self._telemetry_request("GET", path, params=params)
        return Telemetry(**res)

    async def _get_max_data_points(self, class_history_uuid: str) -> int:
        """Get the max data points to use for the telemetry.

        Attempts to get the amount of active time for the workout from the OT Live API. If the workout is not found,
        it will default to 120 data points. If it is found, it will calculate the amount of data points needed based on
        the active time. This should amount to a data point per 30 seconds, roughly.

        Args:
            class_history_uuid (str): The class history UUID.

        Returns:
            int: The max data points to use.
        """
        workouts = await self.get_workouts()
        workout = workouts.by_class_history_uuid.get(class_history_uuid)
        max_data_points = 120 if workout is None else ceil(active_time_to_data_points(workout.active_time))
        return max_data_points

    # the below do not return any data for me, so I can't test them

    async def _get_member_services(self, active_only: bool = True) -> typing.Any:
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's service
        ."""
        active_only_str = "true" if active_only else "false"
        data = await self._default_request(
            "GET", f"/member/members/{self._member_id}/services", params={"activeOnly": active_only_str}
        )
        return data

    async def _get_aspire_data(self, datetime: str | None = None, unit: str | None = None) -> typing.Any:
        """Get data from the member's aspire wearable.

        Note: I don't have an aspire wearable, so I can't test this.

        Args:
            datetime (str | None): The date and time to get data for. Default is None.
            unit (str | None): The measurement unit. Default is None.

        Returns:
            Any: The member's aspire data.
        """
        params = {"datetime": datetime, "unit": unit}

        data = self._default_request("GET", f"/member/wearables/{self._member_id}/wearable-daily", params=params)
        return data

    async def get_body_composition_list(self) -> BodyCompositionList:
        """Get the member's body composition list.

        Returns:
            Any: The member's body composition list.
        """
        data = await self._default_request("GET", f"/member/members/{self._member_uuid}/body-composition")

        return BodyCompositionList(data=data["data"])


def active_time_to_data_points(active_time: int) -> float:
    return active_time / 60 * 2
