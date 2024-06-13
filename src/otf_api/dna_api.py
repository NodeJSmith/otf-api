import typing
from math import ceil

from otf_api.models.responses.dna_hr_history import DnaHrHistory
from otf_api.models.responses.dna_max_hr import DnaMaxHr
from otf_api.models.responses.dna_telemetry import DnaTelemetry

if typing.TYPE_CHECKING:
    from otf_api import Api


class DnaApi:
    def __init__(self, api: "Api"):
        self._api = api
        self.logger = api.logger

        # simplify access to member_id and member_uuid
        self._member_id = self._api.user.member_id
        self._member_uuid = self._api.user.member_uuid

    async def get_hr_history(self) -> DnaHrHistory:
        """Get the heartrate history for the user.

        Returns a list of history items that contain the max heartrate, start/end bpm for each zone,
        the change from the previous, the change bucket, and the assigned at time.

        Returns:
            DnaHrHistory: The heartrate history for the user.

        """
        path = "/v1/physVars/maxHr/history"

        params = {"memberUuid": self._member_id}
        res = await self._api._dna_request("GET", path, params=params)
        return DnaHrHistory(**res)

    async def get_max_hr(self) -> DnaMaxHr:
        """Get the max heartrate for the user.

        Returns a simple object that has the member_uuid and the max_hr.

        Returns:
            DnaMaxHr: The max heartrate for the user.
        """
        path = "/v1/physVars/maxHr"

        params = {"memberUuid": self._member_id}

        res = await self._api._dna_request("GET", path, params=params)
        return DnaMaxHr(**res)

    async def get_telemetry(self, class_history_uuid: str, max_data_points: int = 0) -> DnaTelemetry:
        """Get the telemetry for a class history.

        This returns an object that contains the max heartrate, start/end bpm for each zone,
        and a list of telemetry items that contain the heartrate, splat points, calories, and timestamp.

        Args:
            class_history_uuid (str): The class history UUID.
            max_data_points (int): The max data points to use for the telemetry. Default is 0, which will attempt to\
            get the max data points from the workout. If the workout is not found, it will default to 120 data points.

        Returns:
            DnaTelemetry: The telemetry for the class history.

        """
        path = "/v1/performance/summary"

        max_data_points = max_data_points or await self._get_max_data_points(class_history_uuid)

        params = {"classHistoryUuid": class_history_uuid, "maxDataPoints": max_data_points}
        res = await self._api._dna_request("GET", path, params=params)
        return DnaTelemetry(**res)

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
        workouts = await self._api.member_api.get_workouts()
        workout = workouts.by_class_history_uuid.get(class_history_uuid)
        max_data_points = 120 if workout is None else ceil(active_time_to_data_points(workout.active_time))
        return max_data_points


def active_time_to_data_points(active_time: int) -> float:
    return active_time / 60 * 2
