from datetime import date, datetime, time, timedelta
from logging import getLogger
from typing import Any, Literal

import pendulum

from otf_api import exceptions as exc
from otf_api import filters, models
from otf_api.auth import OtfUser
from otf_api.models.enums import HISTORICAL_BOOKING_STATUSES

from . import utils
from .client import OtfClient

LOGGER = getLogger(__name__)
LOGGED_ONCE: set[str] = set()


class Otf:
    def __init__(self, user: OtfUser | None = None):
        """Initialize the OTF API client.

        Args:
            user (OtfUser): The user to authenticate as.
        """
        self.client = OtfClient(user)

        self.member_uuid = self.client.member_uuid
        self.member = self.get_member_detail()
        self.home_studio = self.member.home_studio
        self.home_studio_uuid = self.home_studio.studio_uuid

    def __eq__(self, other: "Otf | Any") -> bool:  # noqa: ANN401
        """Check if two Otf objects are equal."""
        if not isinstance(other, Otf):
            return False
        return self.member_uuid == other.member_uuid

    def __hash__(self):
        """Return a hash value for the object."""
        # Combine immutable attributes into a single hash value
        return hash(self.member_uuid)

    def get_bookings_new(
        self,
        start_date: datetime | date | str | None = None,
        end_date: datetime | date | str | None = None,
        exclude_cancelled: bool = True,
    ) -> list[models.BookingV2]:
        """Get the bookings for the user.

        If no dates are provided, it will return all bookings between today and 45 days from now.

        Warning:
            ---
        If you do not exclude cancelled bookings, you may receive multiple bookings for the same workout, such
        as when a class changes from a 2G to a 3G. Apparently the system actually creates a new booking for the
        new class, which is normally transparent to the user.

        Args:
            start_date (datetime | date | str | None): The start date for the bookings. Default is None.
            end_date (datetime | date | str | None): The end date for the bookings. Default is None.
            exclude_cancelled (bool): Whether to exclude canceled bookings. Default is True.

        Returns:
            list[BookingV2]: The bookings for the user.
        """
        expand = True  # this doesn't seem to have an effect? so leaving it out of the argument list

        # leaving the parameter as `exclude_canceled` for backwards compatibility
        include_canceled = not exclude_cancelled

        end_date = utils.ensure_datetime(end_date, time(23, 59, 59))
        start_date = utils.ensure_datetime(start_date)

        end_date = end_date or pendulum.today().start_of("day").add(days=45)
        start_date = start_date or pendulum.datetime(1970, 1, 1).start_of("day")

        bookings_resp = self.client.get_bookings_new(
            ends_before=end_date, starts_after=start_date, include_canceled=include_canceled, expand=expand
        )

        return [models.BookingV2.create(**b, api=self) for b in bookings_resp]

    def get_booking_new(self, booking_id: str) -> models.BookingV2:
        """Get a booking by ID."""
        all_bookings = self._get_all_bookings_new()
        booking = next((b for b in all_bookings if b.booking_id == booking_id), None)
        if not booking:
            raise exc.ResourceNotFoundError(f"Booking with ID {booking_id} not found")
        return booking

    def get_classes(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        studio_uuids: list[str] | None = None,
        include_home_studio: bool = True,
        filters: list[filters.ClassFilter] | filters.ClassFilter | None = None,
    ) -> list[models.OtfClass]:
        """Get the classes for the user.

        Returns a list of classes that are available for the user, based on the studio UUIDs provided. If no studio
        UUIDs are provided, it will default to the user's home studio.

        Args:
            start_date (date | str | None): The start date for the classes. Default is None.
            end_date (date | str | None): The end date for the classes. Default is None.
            studio_uuids (list[str] | None): The studio UUIDs to get the classes for. Default is None, which will\
            default to the user's home studio only.
            include_home_studio (bool | None): Whether to include the home studio in the classes. Default is True.
            filters (list[ClassFilter] | ClassFilter | None): A list of filters to apply to the classes, or a single\
            filter. Filters are applied as an OR operation. Default is None.

        Returns:
            list[OtfClass]: The classes for the user.
        """
        start_date = utils.ensure_date(start_date)
        end_date = utils.ensure_date(end_date)
        studio_uuids = utils.get_studio_uuid_list(self.home_studio_uuid, studio_uuids, include_home_studio)

        # get the classes and add the studio details
        classes_resp = self.client.get_classes(studio_uuids)
        studio_dict = self._get_studio_detail_threaded(studio_uuids)
        classes: list[models.OtfClass] = []

        for c in classes_resp:
            c["studio"] = studio_dict[c["studio"]["id"]]  # the one (?) place where ID actually means UUID
            c["is_home_studio"] = c["studio"].studio_uuid == self.home_studio_uuid
            classes.append(models.OtfClass(**c))

        # additional data filtering and enrichment

        # remove those that are cancelled *by the studio*
        classes = [c for c in classes if not c.is_cancelled]

        bookings = self.get_bookings(status=models.BookingStatus.Booked)
        booked_classes = {b.class_uuid for b in bookings}

        for otf_class in classes:
            otf_class.is_booked = otf_class.class_uuid in booked_classes

        # filter by provided start_date/end_date, if provided
        classes = utils.filter_classes_by_date(classes, start_date, end_date)

        # filter by provided filters, if provided
        classes = utils.filter_classes_by_filters(classes, filters)

        # sort by start time, then by name
        classes = sorted(classes, key=lambda x: (x.starts_at, x.name))

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

        data = self.client.get_booking(booking_uuid)
        return models.Booking.create(**data, api=self)

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
        class_uuid = utils.get_class_uuid(otf_class)

        all_bookings = self.get_bookings(exclude_cancelled=False, exclude_checkedin=False)

        if booking := next((b for b in all_bookings if b.class_uuid == class_uuid), None):
            return booking

        raise exc.BookingNotFoundError(f"Booking for class {class_uuid} not found.")

    def get_booking_from_class_new(self, otf_class: str | models.OtfClass | models.BookingV2Class) -> models.BookingV2:
        """Get a specific booking by class_uuid or OtfClass object.

        Args:
            otf_class (str | OtfClass | BookingV2Class): The class UUID or the OtfClass object to get the booking for.

        Returns:
            BookingV2: The booking.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ValueError: If class_uuid is None or empty string.
        """
        class_uuid = utils.get_class_uuid(otf_class)

        all_bookings = self._get_all_bookings_new()

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
        class_uuid = utils.get_class_uuid(otf_class)

        try:
            existing_booking = self.get_booking_from_class(class_uuid)
            if existing_booking.status != models.BookingStatus.Cancelled:
                raise exc.AlreadyBookedError(
                    f"Class {class_uuid} is already booked.", booking_uuid=existing_booking.booking_uuid
                )
        except exc.BookingNotFoundError:
            pass

        if isinstance(otf_class, models.OtfClass):
            bookings = self.get_bookings(start_date=otf_class.starts_at.date(), end_date=otf_class.starts_at.date())
            utils.check_for_booking_conflicts(bookings, otf_class)

        body = {"classUUId": class_uuid, "confirmed": False, "waitlist": False}

        resp = self.client.put_class(class_uuid, body)

        # get the booking uuid - we will only use this to return a Booking object using `get_booking`
        # this is an attempt to improve on OTF's terrible data model
        booking_uuid = resp["savedBookings"][0]["classBookingUUId"]

        booking = self.get_booking(booking_uuid)

        return booking

    def book_class_new(self, class_id: str) -> models.BookingV2:
        """Book a class by providing the class_id.

        Args:
            class_id (str): The class ID to book.

        Returns:
            BookingV2: The booking.
        """
        if not class_id:
            raise ValueError("class_id is required")

        body = {"class_id": class_id, "confirmed": False, "waitlist": False}

        resp = self.client.post_class_new(body)

        new_booking = models.BookingV2.create(**resp, api=self)

        return new_booking

    def cancel_booking(self, booking: str | models.Booking) -> None:
        """Cancel a booking by providing either the booking_uuid or the Booking object.

        Args:
            booking (str | Booking): The booking UUID or the Booking object to cancel.

        Raises:
            ValueError: If booking_uuid is None or empty string
            BookingNotFoundError: If the booking does not exist.
        """
        if isinstance(booking, models.BookingV2):
            LOGGER.warning("BookingV2 object provided, using the new cancel booking endpoint (`cancel_booking_new`)")
            self.cancel_booking_new(booking)

        booking_uuid = utils.get_booking_uuid(booking)

        if booking == booking_uuid:  # ensure this booking exists by calling the booking endpoint
            _ = self.get_booking(booking_uuid)  # allow the exception to be raised if it doesn't exist

        self.client.delete_booking(booking_uuid)

    def cancel_booking_new(self, booking: str | models.BookingV2) -> None:
        """Cancel a booking by providing either the booking_id or the BookingV2 object.

        Args:
            booking (str | BookingV2): The booking ID or the BookingV2 object to cancel.

        Raises:
            ValueError: If booking_id is None or empty string
            BookingNotFoundError: If the booking does not exist.
        """
        if isinstance(booking, models.Booking):
            LOGGER.warning("Booking object provided, using the old cancel booking endpoint (`cancel_booking`)")
            self.cancel_booking(booking)

        booking_id = utils.get_booking_id(booking)

        if booking == booking_id:
            _ = self.get_booking_new(booking_id)  # allow the exception to be raised if it doesn't exist

        self.client.delete_booking_new(booking_id)

    def get_bookings(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        status: models.BookingStatus | list[models.BookingStatus] | None = None,
        exclude_cancelled: bool = True,
        exclude_checkedin: bool = True,
    ) -> list[models.Booking]:
        """Get the member's bookings.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | list[BookingStatus] | None): The status(es) to filter by. Default is None.
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

        if isinstance(status, list):
            status_value = ",".join(status)
        elif isinstance(status, models.BookingStatus):
            status_value = status.value
        elif isinstance(status, str):
            status_value = status
        else:
            status_value = None

        resp = self.client.get_bookings(start_date, end_date, status_value)

        # add studio details for each booking, instead of using the different studio model returned by this endpoint
        studio_uuids = {b["class"]["studio"]["studioUUId"] for b in resp}
        studios = {studio_uuid: self.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids}

        for b in resp:
            b["class"]["studio"] = studios[b["class"]["studio"]["studioUUId"]]
            b["is_home_studio"] = b["class"]["studio"].studio_uuid == self.home_studio_uuid

        bookings = [models.Booking.create(**b, api=self) for b in resp]
        bookings = sorted(bookings, key=lambda x: x.otf_class.starts_at)

        if exclude_cancelled:
            bookings = [b for b in bookings if b.status != models.BookingStatus.Cancelled]

        if exclude_checkedin:
            bookings = [b for b in bookings if b.status != models.BookingStatus.CheckedIn]

        return bookings

    def get_historical_bookings(self) -> list[models.Booking]:
        """Get the member's historical bookings.

        This will go back 45 days and return all bookings for that time period.

        Returns:
            list[Booking]: The member's historical bookings.
        """
        # api goes back 45 days but we'll go back 47 to be safe
        start_date = datetime.today().date() - timedelta(days=47)
        end_date = datetime.today().date()

        return self.get_bookings(
            start_date=start_date,
            end_date=end_date,
            status=HISTORICAL_BOOKING_STATUSES,
            exclude_cancelled=False,
            exclude_checkedin=False,
        )

    def get_member_detail(self) -> models.MemberDetail:
        """Get the member details.

        Returns:
            MemberDetail: The member details.
        """
        data = self.client.get_member_detail()

        # use standard StudioDetail model instead of the one returned by this endpoint
        home_studio_uuid = data["homeStudio"]["studioUUId"]
        data["home_studio"] = self.get_studio_detail(home_studio_uuid)

        return models.MemberDetail.create(**data, api=self)

    def get_member_membership(self) -> models.MemberMembership:
        """Get the member's membership details.

        Returns:
            MemberMembership: The member's membership details.
        """
        data = self.client.get_member_membership()
        return models.MemberMembership(**data)

    def get_member_purchases(self) -> list[models.MemberPurchase]:
        """Get the member's purchases, including monthly subscriptions and class packs.

        Returns:
            list[MemberPurchase]: The member's purchases.
        """
        purchases = self.client.get_member_purchases()

        for p in purchases:
            p["studio"] = self.get_studio_detail(p["studio"]["studioUUId"])

        return [models.MemberPurchase(**purchase) for purchase in purchases]

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

    def get_favorite_studios(self) -> list[models.StudioDetail]:
        """Get the member's favorite studios.

        Returns:
            list[StudioDetail]: The member's favorite studios.
        """
        data = self.client.get_favorite_studios()
        studio_uuids = [studio["studioUUId"] for studio in data]
        return [self.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids]

    def add_favorite_studio(self, studio_uuids: list[str] | str) -> list[models.StudioDetail]:
        """Add a studio to the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to add to the member's favorite\
            studios. If a string is provided, it will be converted to a list.

        Returns:
            list[StudioDetail]: The new favorite studios.
        """
        studio_uuids = utils.ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        resp = self.client.post_favorite_studio(studio_uuids)
        if not resp:
            return []

        new_faves = resp.get("studios", [])

        return [models.StudioDetail.create(**studio, api=self) for studio in new_faves]

    def remove_favorite_studio(self, studio_uuids: list[str] | str) -> None:
        """Remove a studio from the member's favorite studios.

        Args:
            studio_uuids (list[str] | str): The studio UUID or list of studio UUIDs to remove from the member's\
            favorite studios. If a string is provided, it will be converted to a list.

        Returns:
            None
        """
        studio_uuids = utils.ensure_list(studio_uuids)

        if not studio_uuids:
            raise ValueError("studio_uuids is required")

        # keeping the convention of regular/raw methods even though this method doesn't return anything
        # in case that changes in the future
        self.client.delete_favorite_studio(studio_uuids)

    def get_studio_services(self, studio_uuid: str | None = None) -> list[models.StudioService]:
        """Get the services available at a specific studio.

        If no studio UUID is provided, the member's home studio will be used.

        Args:
            studio_uuid (str, optional): The studio UUID to get services for.

        Returns:
            list[StudioService]: The services available at the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid
        data = self.client.get_studio_services(studio_uuid)

        for d in data:
            d["studio"] = self.get_studio_detail(studio_uuid)

        return [models.StudioService(**d) for d in data]

    def get_studio_detail(self, studio_uuid: str | None = None) -> models.StudioDetail:
        """Get detailed information about a specific studio.

        If no studio UUID is provided, it will default to the user's home studio.

        If the studio is not found, it will return a StudioDetail object with default values.

        Args:
            studio_uuid (str, optional): The studio UUID to get detailed information about.

        Returns:
            StudioDetail: Detailed information about the studio.
        """
        studio_uuid = studio_uuid or self.home_studio_uuid

        try:
            res = self.client.get_studio_detail(studio_uuid)
        except exc.ResourceNotFoundError:
            return models.StudioDetail.create_empty_model(studio_uuid)

        return models.StudioDetail.create(**res, api=self)

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

        results = self.client.get_studios_by_geo(latitude, longitude, distance)
        return [models.StudioDetail.create(**studio, api=self) for studio in results]

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
        warning_msg = "This endpoint does not return all data, consider using `get_workouts` instead."
        if warning_msg not in LOGGED_ONCE:
            LOGGER.warning(warning_msg)

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

    def get_sms_notification_settings(self) -> models.SmsNotificationSettings:
        """Get the member's SMS notification settings.

        Returns:
            SmsNotificationSettings: The member's SMS notification settings.
        """
        res = self.client.get_sms_notification_settings(self.member.phone_number)  # type: ignore

        return models.SmsNotificationSettings(**res)

    def update_sms_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.SmsNotificationSettings:
        """Update the member's SMS notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional SMS notifications.
            transactional_enabled (bool | None): Whether to enable transactional SMS notifications.

        Returns:
            SmsNotificationSettings: The updated SMS notification settings.
        """
        current_settings = self.get_sms_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_sms_opt_in
        )
        transactional_enabled = (
            transactional_enabled if transactional_enabled is not None else current_settings.is_transactional_sms_opt_in
        )

        self.client.post_sms_notification_settings(
            self.member.phone_number,  # type: ignore
            promotional_enabled,  # type: ignore
            transactional_enabled,  # type: ignore
        )

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_sms_notification_settings()
        return new_settings

    def get_email_notification_settings(self) -> models.EmailNotificationSettings:
        """Get the member's email notification settings.

        Returns:
            EmailNotificationSettings: The member's email notification settings.
        """
        res = self.client.get_email_notification_settings(self.member.email)  # type: ignore

        return models.EmailNotificationSettings(**res)

    def update_email_notification_settings(
        self, promotional_enabled: bool | None = None, transactional_enabled: bool | None = None
    ) -> models.EmailNotificationSettings:
        """Update the member's email notification settings. Arguments not provided will be left unchanged.

        Args:
            promotional_enabled (bool | None): Whether to enable promotional email notifications.
            transactional_enabled (bool | None): Whether to enable transactional email notifications.

        Returns:
            EmailNotificationSettings: The updated email notification settings.
        """
        current_settings = self.get_email_notification_settings()

        promotional_enabled = (
            promotional_enabled if promotional_enabled is not None else current_settings.is_promotional_email_opt_in
        )
        transactional_enabled = (
            transactional_enabled
            if transactional_enabled is not None
            else current_settings.is_transactional_email_opt_in
        )

        self.client.post_email_notification_settings(
            self.member.email,  # type: ignore
            promotional_enabled,  # type: ignore
            transactional_enabled,  # type: ignore
        )

        # the response returns nothing useful, so we just query the settings again
        new_settings = self.get_email_notification_settings()
        return new_settings

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

        assert first_name is not None, "First name is required"
        assert last_name is not None, "Last name is required"

        res = self.client.put_member_name(first_name, last_name)

        return models.MemberDetail.create(**res, api=self)

    def rate_class(
        self,
        class_uuid: str,
        performance_summary_id: str,
        class_rating: Literal[0, 1, 2, 3],
        coach_rating: Literal[0, 1, 2, 3],
    ) -> None:
        """Rate a class and coach. A simpler method is provided in `rate_class_from_workout`.

        The class rating must be between 0 and 4.
        0 is the same as dismissing the prompt to rate the class/coach in the app.
        1 through 3 is a range from bad to good.

        Args:
            class_uuid (str): The class UUID.
            performance_summary_id (str): The performance summary ID.
            class_rating (int): The class rating. Must be 0, 1, 2, or 3.
            coach_rating (int): The coach rating. Must be 0, 1, 2, or 3.

        Returns:
            None

        """
        body_class_rating = models.get_class_rating_value(class_rating)
        body_coach_rating = models.get_coach_rating_value(coach_rating)

        try:
            self.client.post_class_rating(class_uuid, performance_summary_id, body_class_rating, body_coach_rating)
        except exc.OtfRequestError as e:
            if e.response.status_code == 403:
                raise exc.AlreadyRatedError(f"Workout {performance_summary_id} is already rated.") from None
            raise

    def get_workout_from_booking(self, booking: str | models.BookingV2) -> models.Workout:
        """Get a workout for a specific booking.

        Args:
            booking (str | Booking): The booking ID or BookingV2 object to get the workout for.

        Returns:
            Workout: The member's workout.

        Raises:
            BookingNotFoundError: If the booking does not exist.
            ResourceNotFoundError: If the workout does not exist.
        """
        booking_id = utils.get_booking_id(booking)

        booking = self.get_booking_new(booking_id)

        if not booking.workout or not booking.workout.performance_summary_id:
            raise exc.ResourceNotFoundError(f"Workout for booking {booking_id} not found.")

        perf_summary = self.client.get_performance_summary(booking.workout.performance_summary_id)
        telemetry = self.get_telemetry(booking.workout.performance_summary_id)
        workout = models.Workout.create(**perf_summary, v2_booking=booking, telemetry=telemetry, api=self)

        return workout

    def get_workouts(
        self, start_date: date | str | None = None, end_date: date | str | None = None
    ) -> list[models.Workout]:
        """Get the member's workouts, using the new bookings endpoint and the performance summary endpoint.

        Args:
            start_date (date | str | None): The start date for the workouts. If None, defaults to 30 days ago.
            end_date (date | str | None): The end date for the workouts. If None, defaults to today.

        Returns:
            list[Workout]: The member's workouts.
        """
        start_date = utils.ensure_date(start_date) or pendulum.today().subtract(days=30).date()
        end_date = utils.ensure_date(end_date) or datetime.today().date()

        start_dtme = pendulum.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dtme = pendulum.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        bookings = self.get_bookings_new(start_dtme, end_dtme, exclude_cancelled=False)
        bookings_dict = {b.workout.id: b for b in bookings if b.workout}

        perf_summaries_dict = self.client.get_perf_summaries_threaded(list(bookings_dict.keys()))
        telemetry_dict = self.client.get_telemetry_threaded(list(perf_summaries_dict.keys()))
        perf_summary_to_class_uuid_map = self.client.get_perf_summary_to_class_uuid_mapping()

        workouts: list[models.Workout] = []
        for perf_id, perf_summary in perf_summaries_dict.items():
            workout = models.Workout.create(
                **perf_summary,
                v2_booking=bookings_dict[perf_id],
                telemetry=telemetry_dict.get(perf_id),
                class_uuid=perf_summary_to_class_uuid_map.get(perf_id),
                api=self,
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

        self.rate_class(workout.class_uuid, workout.performance_summary_id, class_rating, coach_rating)

        return self.get_workout_from_booking(workout.booking_id)

    def _get_all_bookings_new(self) -> list[models.BookingV2]:
        """Get bookings from the new endpoint with no date filters.

        This is marked as private to avoid random users calling it.
        Useful for testing and validating models.

        Returns:
            list[BookingV2]: List of bookings that match the search criteria.
        """
        start_date = pendulum.datetime(1970, 1, 1)
        end_date = pendulum.today().start_of("day").add(days=45)
        return self.get_bookings_new(start_date, end_date, exclude_cancelled=False)

    def _get_all_studios(self) -> list[models.StudioDetail]:
        """Gets all studios. Marked as private to avoid random users calling it.

        Useful for testing and validating models.

        Returns:
            list[StudioDetail]: List of studios that match the search criteria.
        """
        # long/lat being None will cause the endpoint to return all studios
        results = self.client.get_studios_by_geo(None, None)
        return [models.StudioDetail.create(**studio, api=self) for studio in results]

    def _get_studio_detail_threaded(self, studio_uuids: list[str]) -> dict[str, models.StudioDetail]:
        """Get detailed information about multiple studios in a threaded manner.

        This is marked as private to avoid random users calling it.
        Useful for testing and validating models.

        Args:
            studio_uuids (list[str]): List of studio UUIDs to get details for.

        Returns:
            dict[str, StudioDetail]: A dictionary mapping studio UUIDs to their detailed information.
        """
        studio_dicts = self.client.get_studio_detail_threaded(studio_uuids)
        return {
            studio_uuid: models.StudioDetail.create(**studio, api=self) for studio_uuid, studio in studio_dicts.items()
        }

    # the below do not return any data for me, so I can't test them

    def _get_member_services(self, active_only: bool = True) -> Any:  # noqa: ANN401
        """Get the member's services.

        Args:
            active_only (bool): Whether to only include active services. Default is True.

        Returns:
            Any: The member's services.
        """
        data = self.client.get_member_services(active_only)
        return data

    def _get_aspire_data(self, datetime: str | None = None, unit: str | None = None) -> Any:  # noqa: ANN401
        """Get data from the member's aspire wearable.

        Note: I don't have an aspire wearable, so I can't test this.

        Args:
            datetime (str | None): The date and time to get data for. Default is None.
            unit (str | None): The measurement unit. Default is None.

        Returns:
            Any: The member's aspire data.
        """
        data = self.client.get_aspire_data(datetime, unit)
        return data
