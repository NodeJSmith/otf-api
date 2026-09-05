import typing
from datetime import date

import pendulum

from otf_api.api import utils
from otf_api.models.trends import (
    TrendType,
    WorkoutStatsPreviewResponse,
    WorkoutStatsResponse,
)

from .trend_client import TrendClient

if typing.TYPE_CHECKING:
    from otf_api import Otf
    from otf_api.api.client import OtfClient

DEFAULT_PREVIEW_WORKOUT_COUNT = 10


class TrendApi:
    """API for retrieving workout trend data from OrangeTheory.

    Provides methods to get per-metric trend data (splat points, heart rate,
    treadmill speed, rower stats) over time, as well as a preview across all metrics.
    """

    def __init__(self, otf: "Otf", otf_client: "OtfClient"):
        self.otf = otf
        self.client = TrendClient(otf_client)

    def get_workout_stats(
        self,
        trend_type: TrendType,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> WorkoutStatsResponse:
        """Get detailed workout stats for a specific metric over a date range.

        Args:
            trend_type: The trend metric to retrieve (e.g. TrendType.SplatPoints).
            start_date: Start of the date range. Defaults to 90 days ago.
            end_date: End of the date range. Defaults to today.

        Returns:
            WorkoutStatsResponse: The stat data with individual data points per workout.
        """
        if not isinstance(trend_type, TrendType):
            raise TypeError(f"trend_type must be a TrendType enum member, got {type(trend_type).__name__}")

        start = utils.ensure_date(start_date) or pendulum.today().subtract(days=90).date()
        end = utils.ensure_date(end_date) or pendulum.today().date()

        start_str = pendulum.instance(pendulum.datetime(start.year, start.month, start.day)).to_iso8601_string()
        end_str = pendulum.instance(pendulum.datetime(end.year, end.month, end.day, 23, 59, 59)).to_iso8601_string()

        stats_key = utils.validate_identifier(trend_type.value, "stats_key")
        data = self.client.get_workout_stats(stats_key, start_str, end_str)
        return WorkoutStatsResponse(**data)

    def get_workout_stats_preview(
        self, workout_count: int = DEFAULT_PREVIEW_WORKOUT_COUNT
    ) -> WorkoutStatsPreviewResponse:
        """Get a preview of workout stats across all trend metrics.

        Args:
            workout_count: Number of recent workouts to include. Default is 10.

        Returns:
            WorkoutStatsPreviewResponse: Preview data with stats across all metrics.
        """
        data = self.client.get_workout_stats_preview(workout_count)
        return WorkoutStatsPreviewResponse(**data)
