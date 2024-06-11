import typing
from datetime import date

from otf.models.responses.enums import ClassStatus
from otf.models.responses.favorite_studios import FavoriteStudioList

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
    from otf import Api


class MemberApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid

    async def get_workouts(self) -> WorkoutList:
        """Get the list of workouts from OT Live.

        This returns data from the same api the OT Live website uses. It is quite a bit of data,
        and all workouts going back to ~2019. The data includes the class history UUID, which can be used to get
        telemetry data for a specific workout.

        Returns:
            WorkoutList: The list of workouts.
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
        statuses: list[ClassStatus] | None = None,
    ) -> BookingList:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            statuses (list[ClassStatus] | None): The statuses of the bookings to get. Default is None.

        Returns:
            BookingList: The member's bookings.
        """

        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        status_values = [status.value for status in statuses] if statuses else None

        params = {"startDate": start_date, "endDate": end_date, "statuses": status_values}

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

        Note: I'm not sure what the challenge_sub_type_id is supposed to be, so it defaults to 0.

        Args:
            equipment_id (EquipmentType): The equipment ID.
            challenge_type_id (ChallengeType): The challenge type ID.
            challenge_sub_type_id (int): The challenge sub type ID. Default is 0.

        Returns:
            ChallengeTrackerDetailList: The member's challenge tracker details.
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

    async def get_challenge_tracker_participation(self, challenge_type_id: ChallengeType) -> dict:
        """Get the member's participation in a challenge.

        Note: I've never gotten this to return anything other than invalid response. I'm not sure if it's a bug
        in my code or the API.

        Args:
            challenge_type_id (ChallengeType): The challenge type ID.

        Returns:
            dict: The member's participation in the challenge.
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

        The member_id parameter is optional. If not provided, the currently logged in user will be used. The
        include_addresses, include_class_summary, and include_credit_card parameters are optional and determine
        what additional information is included in the response. By default, all additional information is included,
        with the exception of the credit card information.

        Note: The base member details include the last four of a credit card regardless of the include_credit_card,
        although this is not always the same details as what is in the member_credit_card field. There doesn't seem
        to be a way to exclude this information, and I do not know which is which or why they differ.

        Args:
            include_addresses (bool): Whether to include the member's addresses in the response.
            include_class_summary (bool): Whether to include the member's class summary in the response.
            include_credit_card (bool): Whether to include the member's credit card information in the response.

        Returns:
            MemberDetail: The member details.
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

        Note: latest agreement here means a specific agreement id, not the most recent agreement.

        Returns:
            LatestAgreement: The agreement.
        """
        data = await self._api._default_request("GET", "/member/agreements/9d98fb27-0f00-4598-ad08-5b1655a59af6")
        return LatestAgreement(**data["data"])

    async def get_studio_services(self, studio_uuid: str | None = None) -> StudioServiceList:
        """Get the services available at a specific studio. If no studio UUID is provided, the member's home studio
        will be used.

        Args:
            studio_uuid (str): The studio UUID to get services for. Default is None, which will use the member's home
            studio.

        Returns:
            StudioServiceList: The services available at the studio.
        """
        studio_uuid = studio_uuid or self._api.home_studio_uuid
        data = await self._api._default_request("GET", f"/member/studios/{studio_uuid}/services")
        return StudioServiceList(data=data["data"])

    # the below do not return any data for me, so I can't test them

    async def get_member_services(self, active_only: bool = True) -> dict:
        """Get the member's services.

        Note: I'm not sure what the services are, as I don't have any data to test this with.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            dict: The member's service
        ."""
        active_only_str = "true" if active_only else "false"
        data = await self._api._default_request(
            "GET", f"/member/members/{self._member_id}/services", params={"activeOnly": active_only_str}
        )
        return data

    async def get_aspire_data(self, datetime: str | None = None, unit: str | None = None) -> dict:
        """Get data from the member's aspire wearable.

        Note: I don't have an aspire wearable, so I can't test this.

        Args:
            datetime (str | None): The date and time to get data for. Default is None.
            unit (str | None): The measurement unit. Default is None.

        Returns:
            dict: The member's aspire data.
        """
        params = {"datetime": datetime, "unit": unit}

        data = self._api._default_request("GET", f"/member/wearables/{self._member_id}/wearable-daily", params=params)
        return data

    async def get_body_composition_list(self) -> dict:
        """Get the member's body composition list.

        Note: I don't have body composition data, so I can't test this.

        Returns:
            dict: The member's body composition list.
        """
        data = await self._api._default_request("GET", f"/member/members/{self._member_uuid}/body-composition")
        return data
