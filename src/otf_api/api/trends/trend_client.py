from typing import Any

from otf_api.api.client import API_GATEWAY_BASE_URL, OtfClient


class TrendClient:
    """Client for retrieving workout trends/stats data from the OTF Gateway API."""

    def __init__(self, client: OtfClient):
        self.client = client

    def gateway_request(
        self, method: str, path: str, params: dict[str, Any] | None = None, headers: dict[str, Any] | None = None
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the Gateway API."""
        return self.client.do(method, API_GATEWAY_BASE_URL, path, params, headers=headers)

    def get_workout_stats(self, stats_key: str, start_date: str, end_date: str) -> dict:
        """Retrieve workout stats for a specific metric over a date range.

        Args:
            stats_key: The stat key (e.g. 'splat_points', 'average_hr').
            start_date: ISO-format start date.
            end_date: ISO-format end date.
        """
        return self.gateway_request(
            "GET",
            f"/consumer-mobile/v1/users/me/workout-stats/{stats_key}",
            params={"start": start_date, "end": end_date},
        )

    def get_workout_stats_preview(self, workout_count: int = 10) -> dict:
        """Retrieve a preview of workout stats across all metrics.

        Args:
            workout_count: Number of recent workouts to include. Default is 10.
        """
        return self.gateway_request(
            "GET",
            "/consumer-mobile/v1/users/me/workout-stats/preview",
            params={"workoutCount": workout_count},
        )
