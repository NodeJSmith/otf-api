import typing
from datetime import date

from otf_api.models.responses.enums import BookingStatus
from otf_api.models.responses.favorite_studios import FavoriteStudioList

from .models import (
    BookingList,
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

if typing.TYPE_CHECKING:
    from otf_api import Api


class MemberApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid

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

        res = await self._api._default_request("GET", "/virtual-class/in-studio-workouts")

        return WorkoutList(workouts=res["data"])

    async def get_total_classes(self) -> TotalClasses:
        """Get the member's total classes. This is a simple object reflecting the total number of classes attended,
        both in-studio and OT Live.

        Returns:
            TotalClasses: The member's total classes.
        """
        data = await self._api._default_request("GET", "/mobile/v1/members/classes/summary")
        return TotalClasses(**data["data"])

    async def get_bookings(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        status: BookingStatus | None = None,
    ) -> BookingList:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | None): The status of the bookings to get. Default is None, which includes\
            all statuses. Only a single status can be provided.

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
            date range. If no dates are provided, it seems to default to the current month.

            In general, this endpoint does not seem to be able to access bookings older than a certain point. It seems
            to be able to go back about 45 days or a month. For current/future dates, it seems to be able to go forward
            to as far as you can book classes in the app, which is usually 30 days from today's date.

        Developer Notes:
            ---
            Looking at the code in the app, it appears that this endpoint accepts multiple statuses. Indeed,
            it does not throw an error if you include a list of statuses. However, only the last status in the list is
            used. I'm not sure if this is a bug or if the API is supposed to work this way.
        """

        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        status_value = status.value if status else None

        params = {"startDate": start_date, "endDate": end_date, "statuses": status_value}

        res = await self._api._default_request("GET", f"/member/members/{self._member_id}/bookings", params=params)

        return BookingList(bookings=res["data"])

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

        res = await self._api._default_request("GET", f"/member/members/{self._member_id}/bookings", params=params)

        return BookingList(bookings=res["data"])

    async def get_challenge_tracker_content(self) -> ChallengeTrackerContent:
        """Get the member's challenge tracker content.

        Returns:
            ChallengeTrackerContent: The member's challenge tracker content.
        """
        data = await self._api._default_request("GET", f"/challenges/v3.1/member/{self._member_id}")
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

        data = await self._api._default_request(
            "GET", f"/challenges/v3/member/{self._member_id}/benchmarks", params=params
        )

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

        data = await self._api._default_request(
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

        data = await self._api._default_request("GET", f"/member/members/{self._member_id}", params=params)
        return MemberDetail(**data["data"])

    async def get_member_membership(self) -> MemberMembership:
        """Get the member's membership details.

        Returns:
            MemberMembership: The member's membership details.
        """

        data = await self._api._default_request("GET", f"/member/members/{self._member_id}/memberships")
        return MemberMembership(**data["data"])

    async def get_member_purchases(self) -> MemberPurchaseList:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            MemberPurchaseList: The member's purchases.
        """
        data = await self._api._default_request("GET", f"/member/members/{self._member_id}/purchases")
        return MemberPurchaseList(data=data["data"])

    async def get_out_of_studio_workout_history(self) -> OutOfStudioWorkoutHistoryList:
        """Get the member's out of studio workout history.

        Returns:
            OutOfStudioWorkoutHistoryList: The member's out of studio workout history.
        """
        data = await self._api._default_request("GET", f"/member/members/{self._member_id}/out-of-studio-workout")

        return OutOfStudioWorkoutHistoryList(data=data["data"])

    async def get_favorite_studios(self) -> FavoriteStudioList:
        """Get the member's favorite studios.

        Returns:
            FavoriteStudioList: The member's favorite studios.
        """
        data = await self._api._default_request("GET", f"/member/members/{self._member_id}/favorite-studios")

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
        data = await self._api._default_request("GET", "/member/agreements/9d98fb27-0f00-4598-ad08-5b1655a59af6")
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
        studio_uuid = studio_uuid or self._api.home_studio.studio_uuid
        data = await self._api._default_request("GET", f"/member/studios/{studio_uuid}/services")
        return StudioServiceList(data=data["data"])

    # the below do not return any data for me, so I can't test them

    async def _get_member_services(self, active_only: bool = True) -> typing.Any:
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's service
        ."""
        active_only_str = "true" if active_only else "false"
        data = await self._api._default_request(
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

        data = self._api._default_request("GET", f"/member/wearables/{self._member_id}/wearable-daily", params=params)
        return data

    async def _get_body_composition_list(self) -> typing.Any:
        """Get the member's body composition list.

        Note: I don't have body composition data, so I can't test this.

        Returns:
            Any: The member's body composition list.
        """
        data = await self._api._default_request("GET", f"/member/members/{self._member_uuid}/body-composition")
        return data
