import typing
from datetime import date, datetime, time, timedelta
from logging import getLogger
from typing import Literal

import pendulum

from otf_api import exceptions as exc
from otf_api import models
from otf_api.api import utils
from otf_api.api.client import OtfClient
from otf_api.models.bookings import HISTORICAL_BOOKING_STATUSES, ClassFilter

from .booking_client import BookingClient

if typing.TYPE_CHECKING:
    from otf_api import Otf

LOGGER = getLogger(__name__)


class BookingApi:
    def __init__(self, otf: "Otf", otf_client: OtfClient):
        """Initialize the Booking API client.

        Args:
            otf (Otf): The OTF API client.
            otf_client (OtfClient): The OTF client to use for requests.
        """
        self.otf = otf
        self.client = BookingClient(otf_client)

    def get_bookings_new(
        self,
        start_date: datetime | date | str | None = None,
        end_date: datetime | date | str | None = None,
        exclude_cancelled: bool = True,
        remove_duplicates: bool = True,
    ) -> list[models.BookingV2]:
        """Get the bookings for the user.

        If no dates are provided, it will return all bookings between today and 45 days from now.

        Args:
            start_date (datetime | date | str | None): The start date for the bookings. Default is None.
            end_date (datetime | date | str | None): The end date for the bookings. Default is None.
            exclude_cancelled (bool): Whether to exclude cancelled bookings. Default is True.
            remove_duplicates (bool): When True, only keeps the most recent booking for a given class_id.\
                This is helpful to avoid duplicates caused by cancel/rebook scenarios, class changes, etc.\
                Default is True.

        Returns:
            list[BookingV2]: The bookings for the user.

        Note:
            Setting `exclude_cancelled` to `False` will return all bookings, which may result in multiple bookings for\
            the same `class_id`. Setting `exclude_cancelled` to `True` will prevent this, but has the side effect of\
            not returning *any* results for a cancelled (and not rebooked) booking. If you want a unique list of\
            bookings that includes cancelled bookings, you should set `exclude_cancelled` to `False` and\
            `remove_duplicates` to `True`.

        Warning:
            If you do not set either `exclude_cancelled` or `remove_duplicates` to True you may receive multiple\
            bookings for the same workout. This will happen if you cancel and rebook or if a class changes, such\
            as from a 2G to a 3G. Apparently the system actually creates a new booking for the new class, which\
             is normally transparent to the user.
        """
        expand = True  # this doesn't seem to have an effect? so leaving it out of the argument list

        # leaving the parameter as `exclude_canceled` for backwards compatibility
        include_canceled = not exclude_cancelled

        end_date = utils.ensure_datetime(end_date, time(23, 59, 59))
        start_date = utils.ensure_datetime(start_date)

        end_date = end_date or pendulum.today().start_of("day").add(days=45)
        start_date = start_date or pendulum.today().start_of("day")

        bookings_resp = self.client.get_bookings_new(
            ends_before=end_date, starts_after=start_date, include_canceled=include_canceled, expand=expand
        )

        results = [models.BookingV2.create(**b, api=self.otf) for b in bookings_resp]

        if not remove_duplicates:
            return results

        # remove duplicates by class_id, keeping the one with the most recent updated_at timestamp
        seen_classes: dict[str, models.BookingV2] = {}

        for booking in results:
            class_id = booking.otf_class.class_id
            if class_id not in seen_classes:
                seen_classes[class_id] = booking
                continue

            existing_booking = seen_classes[class_id]
            if exclude_cancelled:
                LOGGER.warning(
                    f"Duplicate class_id {class_id} found when `exclude_cancelled` is True, "
                    "this is unexpected behavior."
                )
            if booking.updated_at > existing_booking.updated_at:
                seen_classes[class_id] = booking

        results = list(seen_classes.values())
        results = sorted(results, key=lambda x: x.starts_at)

        return results

    def get_bookings_new_by_date(
        self,
        start_date: datetime | date | str | None = None,
        end_date: datetime | date | str | None = None,
    ) -> dict[datetime, models.BookingV2]:
        """Get the bookings for the user, returned in a dictionary keyed by start datetime.

        This is a convenience method that calls `get_bookings_new` and returns a dictionary instead\
        of a list. Because this returns a dictionary, it will only return the most recent booking for each class_id.
        It will also include cancelled bookings.

        Returns:
            dict[datetime, BookingV2]: A dictionary of bookings keyed by their start datetime.
        """
        bookings = self.get_bookings_new(
            start_date=start_date,
            end_date=end_date,
            exclude_cancelled=False,
            remove_duplicates=True,
        )

        bookings_by_date = {b.starts_at: b for b in bookings}
        return bookings_by_date

    def get_booking_new(self, booking_id: str) -> models.BookingV2:
        """Get a booking by ID from the new bookings endpoint.

        Args:
            booking_id (str): The booking ID to get.

        Returns:
            BookingV2: The booking.

        Raises:
            ValueError: If booking_id is None or empty string.
            ResourceNotFoundError: If the booking with the given ID does not exist.
        """
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
        filters: list[ClassFilter] | ClassFilter | None = None,
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
        studio_uuids = utils.get_studio_uuid_list(self.otf.home_studio_uuid, studio_uuids, include_home_studio)

        # get the classes and add the studio details
        classes_resp = self.client.get_classes(studio_uuids)
        studio_dict = self.otf.studios._get_studio_detail_threaded(studio_uuids)
        classes: list[models.OtfClass] = []

        for c in classes_resp:
            c["studio"] = studio_dict[c["studio"]["id"]]  # the one (?) place where ID actually means UUID
            c["is_home_studio"] = c["studio"].studio_uuid == self.otf.home_studio_uuid
            classes.append(models.OtfClass.create(**c, api=self.otf))

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
        """Get a specific booking by booking_uuid, from the old bookings endpoint.

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
        return models.Booking.create(**data, api=self.otf)

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

        resp = self.client.put_class(body)

        # get the booking uuid - we will only use this to return a Booking object using `get_booking`
        # this is an attempt to improve on OTF's terrible data model
        booking_uuid = resp["savedBookings"][0]["classBookingUUId"]

        booking = self.get_booking(booking_uuid)

        return booking

    def book_class_new(self, class_id: str | models.BookingV2Class) -> models.BookingV2:
        """Book a class by providing either the class_id or the BookingV2Class object.

        This uses the new booking endpoint.

        Args:
            class_id (str): The class ID to book.

        Returns:
            BookingV2: The booking.

        Raises:
            OtfException: If there is an error booking the class.
            TypeError: If the input is not a string or BookingV2Class.
        """
        class_id = utils.get_class_id(class_id)

        body = {"class_id": class_id, "confirmed": False, "waitlist": False}

        resp = self.client.post_class_new(body)

        new_booking = models.BookingV2.create(**resp, api=self.otf)

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

        If no dates are provided, it will return all bookings between today and 45 days from now.

        Args:
            start_date (date | str | None): The start date for the bookings. Default is None.
            end_date (date | str | None): The end date for the bookings. Default is None.
            status (BookingStatus | list[BookingStatus] | None): The status(es) to filter by. Default is None.
            exclude_cancelled (bool): Whether to exclude cancelled bookings. Default is True.
            exclude_checkedin (bool): Whether to exclude checked-in bookings. Default is True.

        Returns:
            list[Booking]: The member's bookings.

        Warning:
            Incorrect statuses do not cause any bad status code, they just return no results.

        Tip:
            `CheckedIn` - you must provide dates if you want to get bookings with a status of CheckedIn. If you do not
            provide dates, the endpoint will return no results for this status.
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
        studios = {studio_uuid: self.otf.studios.get_studio_detail(studio_uuid) for studio_uuid in studio_uuids}

        for b in resp:
            b["class"]["studio"] = studios[b["class"]["studio"]["studioUUId"]]
            b["is_home_studio"] = b["class"]["studio"].studio_uuid == self.otf.home_studio_uuid

        bookings = [models.Booking.create(**b, api=self.otf) for b in resp]
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

    def _get_all_bookings_new(
        self, exclude_cancelled: bool = True, remove_duplicates: bool = True
    ) -> list[models.BookingV2]:
        """Get bookings from the new endpoint with no date filters.

        This is marked as private to avoid random users calling it.
        Useful for testing and validating models.

        Args:
            exclude_cancelled (bool): Whether to exclude cancelled bookings. Default is True.
            remove_duplicates (bool): Whether to remove duplicate bookings. Default is True.

        Returns:
            list[BookingV2]: List of bookings that match the search criteria.
        """
        start_date = pendulum.datetime(1970, 1, 1)
        end_date = pendulum.today().start_of("day").add(days=45)
        return self.get_bookings_new(start_date, end_date, exclude_cancelled, remove_duplicates)

    def _get_all_bookings_new_by_date(self) -> dict[datetime, models.BookingV2]:
        """Get all bookings from the new endpoint by date.

        This is marked as private to avoid random users calling it.
        Useful for testing and validating models.

        Returns:
            dict[datetime, BookingV2]: Dictionary of bookings by date.
        """
        start_date = pendulum.datetime(1970, 1, 1)
        end_date = pendulum.today().start_of("day").add(days=45)
        bookings = self.get_bookings_new_by_date(start_date, end_date)
        return bookings
