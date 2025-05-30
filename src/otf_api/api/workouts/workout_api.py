import typing
import warnings
from datetime import date, datetime
from logging import getLogger
from typing import Any, Literal

import pendulum

from otf_api import exceptions as exc
from otf_api import models
from otf_api.api import utils
from otf_api.api.client import OtfClient

from .workout_client import WorkoutClient

if typing.TYPE_CHECKING:
    from otf_api import Otf

LOGGER = getLogger(__name__)


class WorkoutApi:
    def __init__(self, otf: "Otf", otf_client: OtfClient):
        """Initialize the Workout API client.

        Args:
            otf (Otf): The OTF API client.
            otf_client (OtfClient): The OTF client to use for requests.
        """
        self.otf = otf
        self.client = WorkoutClient(otf_client)

    def get_body_composition_list(self) -> list[models.BodyCompositionData]:
        """Get the member's body composition list.

        Returns:
            list[BodyCompositionData]: The member's body composition list.
        """
        data = self.client.get_body_composition_list()
        return [models.BodyCompositionData(**item) for item in data]

    def get_challenge_tracker(self) -> models.ChallengeTracker:
        """Get the member's challenge tracker content.

        Returns:
            ChallengeTracker: The member's challenge tracker content.
        """
        data = self.client.get_challenge_tracker()
        return models.ChallengeTracker(**data["Dto"])

    def get_benchmarks(
        self,
        challenge_category_id: int = 0,
        equipment_id: models.EquipmentType | Literal[0] = 0,
        challenge_subcategory_id: int = 0,
    ) -> list[models.FitnessBenchmark]:
        """Get the member's challenge tracker participation details.

        Args:
            challenge_category_id (int): The challenge type ID.
            equipment_id (EquipmentType | Literal[0]): The equipment ID, default is 0 - this doesn't seem\
                to be have any impact on the results.
            challenge_subcategory_id (int): The challenge sub type ID. Default is 0 - this doesn't seem\
                to be have any impact on the results.

        Returns:
            list[FitnessBenchmark]: The member's challenge tracker details.
        """
        data = self.client.get_benchmarks(int(challenge_category_id), int(equipment_id), challenge_subcategory_id)
        return [models.FitnessBenchmark(**item) for item in data]

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

    def get_benchmarks_by_challenge_category(self, challenge_category_id: int) -> list[models.FitnessBenchmark]:
        """Get the member's challenge tracker participation details by challenge.

        Args:
            challenge_category_id (int): The challenge type ID.

        Returns:
            list[FitnessBenchmark]: The member's challenge tracker details.
        """
        benchmarks = self.get_benchmarks(challenge_category_id=challenge_category_id)

        benchmarks = [b for b in benchmarks if b.challenge_category_id == challenge_category_id]

        return benchmarks

    def get_challenge_tracker_detail(self, challenge_category_id: int) -> models.FitnessBenchmark:
        """Get details about a challenge.

        This endpoint does not (usually) return member participation, but rather details about the challenge itself.

        Args:
            challenge_category_id (int): The challenge type ID.

        Returns:
            FitnessBenchmark: Details about the challenge.
        """
        data = self.client.get_challenge_tracker_detail(int(challenge_category_id))

        if len(data) > 1:
            LOGGER.warning("Multiple challenge participations found, returning the first one.")

        if len(data) == 0:
            raise exc.ResourceNotFoundError(f"Challenge {challenge_category_id} not found")

        return models.FitnessBenchmark(**data[0])

    def get_performance_summary(self, performance_summary_id: str) -> models.PerformanceSummary:
        """Get the details for a performance summary. Generally should not be called directly. This.

        Args:
            performance_summary_id (str): The performance summary ID.

        Returns:
            dict[str, Any]: The performance summary details.
        """
        warnings.warn(
            "`This endpoint does not return all data, consider using `get_workouts` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        resp = self.client.get_performance_summary(performance_summary_id)
        return models.PerformanceSummary(**resp)

    def get_hr_history(self) -> list[models.TelemetryHistoryItem]:
        """Get the heartrate history for the user.

        Returns a list of history items that contain the max heartrate, start/end bpm for each zone,
        the change from the previous, the change bucket, and the assigned at time.

        Returns:
            list[HistoryItem]: The heartrate history for the user.

        """
        resp = self.client.get_hr_history_raw()
        return [models.TelemetryHistoryItem(**item) for item in resp]

    def get_telemetry(self, performance_summary_id: str, max_data_points: int = 150) -> models.Telemetry:
        """Get the telemetry for a performance summary.

        This returns an object that contains the max heartrate, start/end bpm for each zone,
        and a list of telemetry items that contain the heartrate, splat points, calories, and timestamp.

        Args:
            performance_summary_id (str): The performance summary id.
            max_data_points (int): The max data points to use for the telemetry. Default is 150, to match the app.

        Returns:
            TelemetryItem: The telemetry for the class history.
        """
        res = self.client.get_telemetry(performance_summary_id, max_data_points)
        return models.Telemetry(**res)

    def get_member_lifetime_stats_in_studio(
        self, select_time: models.StatsTime = models.StatsTime.AllTime
    ) -> models.InStudioStatsData:
        """Get the member's lifetime stats in studio.

        Args:
            select_time (StatsTime): The time period to get stats for. Default is StatsTime.AllTime.

        Returns:
            InStudioStatsData: The member's lifetime stats in studio.
        """
        data = self.client.get_member_lifetime_stats(select_time.value)

        stats = models.StatsResponse(**data)

        return stats.in_studio.get_by_time(select_time)

    def get_member_lifetime_stats_out_of_studio(
        self, select_time: models.StatsTime = models.StatsTime.AllTime
    ) -> models.OutStudioStatsData:
        """Get the member's lifetime stats out of studio.

        Args:
            select_time (StatsTime): The time period to get stats for. Default is StatsTime.AllTime.

        Returns:
            OutStudioStatsData: The member's lifetime stats out of studio.
        """
        data = self.client.get_member_lifetime_stats(select_time.value)

        stats = models.StatsResponse(**data)

        return stats.out_studio.get_by_time(select_time)

    def get_out_of_studio_workout_history(self) -> list[models.OutOfStudioWorkoutHistory]:
        """Get the member's out of studio workout history.

        Returns:
            list[OutOfStudioWorkoutHistory]: The member's out of studio workout history.
        """
        data = self.client.get_out_of_studio_workout_history()

        return [models.OutOfStudioWorkoutHistory(**workout) for workout in data]

    def get_workout_from_booking(self, booking: str | models.BookingV2) -> models.Workout:
        """Get a workout for a specific booking.

        Args:
            booking (str | Booking): The booking ID or BookingV2 object to get the workout for.

        Returns:
            Workout: The member's workout.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ResourceNotFoundError: If the workout does not exist.
            TypeError: If the booking is an old Booking model, as these do not have the necessary fields.
        """
        if isinstance(booking, models.Booking):
            raise TypeError("This method cannot be used with the old Booking model")

        booking_id = utils.get_booking_id(booking)

        booking = self.otf.bookings.get_booking_new(booking_id)

        if not booking.workout or not booking.workout.performance_summary_id:
            raise exc.ResourceNotFoundError(f"Workout for booking {booking_id} not found.")

        perf_summary = self.client.get_performance_summary(booking.workout.performance_summary_id)
        telemetry = self.get_telemetry(booking.workout.performance_summary_id)
        workout = models.Workout.create(**perf_summary, v2_booking=booking, telemetry=telemetry, api=self.otf)

        return workout

    def get_workouts(
        self, start_date: date | str | None = None, end_date: date | str | None = None, max_data_points: int = 150
    ) -> list[models.Workout]:
        """Get the member's workouts, using the new bookings endpoint and the performance summary endpoint.

        Args:
            start_date (date | str | None): The start date for the workouts. If None, defaults to 30 days ago.
            end_date (date | str | None): The end date for the workouts. If None, defaults to today.
            max_data_points (int): The maximum number of data points to return for the telemetry. Default is 150.

        Returns:
            list[Workout]: The member's workouts.
        """
        start_date = utils.ensure_date(start_date) or pendulum.today().subtract(days=30).date()
        end_date = utils.ensure_date(end_date) or datetime.today().date()

        start_dtme = pendulum.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dtme = pendulum.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        bookings = self.otf.bookings.get_bookings_new(
            start_dtme, end_dtme, exclude_cancelled=True, remove_duplicates=True
        )
        bookings_dict = {b.workout.id: b for b in bookings if b.workout}

        perf_summaries_dict = self.client.get_perf_summaries_threaded(list(bookings_dict.keys()))
        telemetry_dict = self.client.get_telemetry_threaded(list(perf_summaries_dict.keys()), max_data_points)
        perf_summary_to_class_uuid_map = self.client.get_perf_summary_to_class_uuid_mapping()

        workouts: list[models.Workout] = []
        for perf_id, perf_summary in perf_summaries_dict.items():
            workout = models.Workout.create(
                **perf_summary,
                v2_booking=bookings_dict[perf_id],
                telemetry=telemetry_dict.get(perf_id),
                class_uuid=perf_summary_to_class_uuid_map.get(perf_id),
                api=self.otf,
            )
            workouts.append(workout)

        return workouts

    def rate_class_from_workout(
        self,
        workout: models.Workout,
        class_rating: Literal[0, 1, 2, 3],
        coach_rating: Literal[0, 1, 2, 3],
    ) -> models.Workout:
        """Rate a class and coach.

        The class rating must be 0, 1, 2, or 3. 0 is the same as dismissing the prompt to rate the class/coach. 1 - 3\
            is a range from bad to good.

        Args:
            workout (Workout): The workout to rate.
            class_rating (int): The class rating. Must be 0, 1, 2, or 3.
            coach_rating (int): The coach rating. Must be 0, 1, 2, or 3.

        Returns:
            Workout: The updated workout with the new ratings.

        Raises:
            AlreadyRatedError: If the performance summary is already rated.
            ClassNotRatableError: If the performance summary is not rateable.
        """
        if not workout.ratable or not workout.class_uuid:
            raise exc.ClassNotRatableError(f"Workout {workout.performance_summary_id} is not rateable.")

        if workout.class_rating is not None or workout.coach_rating is not None:
            raise exc.AlreadyRatedError(f"Workout {workout.performance_summary_id} already rated.")

        self.otf.bookings.rate_class(workout.class_uuid, workout.performance_summary_id, class_rating, coach_rating)

        return self.get_workout_from_booking(workout.booking_id)

    # the below do not return any data for me, so I can't test them

    def _get_aspire_data(self, datetime: str | None = None, unit: str | None = None) -> Any:  # noqa: ANN401
        """Get data from the member's aspire wearable.

        Args:
            datetime (str | None): The date and time to get data for. Default is None.
            unit (str | None): The measurement unit. Default is None.

        Returns:
            Any: The member's aspire data.

        Note:
            I don't have an aspire wearable, so I can't test this.
        """
        data = self.client.get_aspire_data(datetime, unit)
        return data
