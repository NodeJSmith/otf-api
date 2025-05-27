from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from otf_api.api.client import API_IO_BASE_URL, API_TELEMETRY_BASE_URL, CACHE, OtfClient


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
