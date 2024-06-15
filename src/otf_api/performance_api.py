import typing

from otf_api.models.responses.performance_summary_detail import PerformanceSummaryDetail
from otf_api.models.responses.performance_summary_list import PerformanceSummaryList

if typing.TYPE_CHECKING:
    from otf_api import Api


class PerformanceApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid
        self._headers = {"koji-member-id": self._member_id, "koji-member-email": self._api.user.id_claims_data.email}

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
        res = await self._api._performance_summary_request("GET", path, headers=self._headers, params=params)
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
        res = await self._api._performance_summary_request("GET", path, headers=self._headers)
        retval = PerformanceSummaryDetail(**res)
        return retval
