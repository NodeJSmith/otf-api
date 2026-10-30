"""Tests for BookingApi read-only methods."""

from datetime import date, datetime
from unittest.mock import patch

import httpx
import pendulum
import pytest
from conftest import load_fixture
from pydantic import ValidationError

from otf_api.exceptions import AlreadyBookedError, ConflictingBookingError, ResourceNotFoundError
from otf_api.models.bookings import Booking, BookingV2, BookingV2Class, ClassFilter, OtfClass
from otf_api.models.bookings.bookings_v2 import get_end_time
from otf_api.models.bookings.enums import BookingStatus, ClassType
from otf_api.models.studios import StudioDetail, StudioStatus
from otf_api.models.vocabulary import reported_values
from otf_api.models.workouts import EquipmentType, FitnessBenchmark

_CLASSES_URL = "https://api.orangetheory.io/v1/classes?studio_ids=452ec40a-3193-4a54-ae89-71105e503a67"
_BOOKINGS_NEW_DATE_PARAMS = "2026-03-27"
_BOOKINGS_NEW_URL = (
    "https://api.orangetheory.io/v1/bookings/me"
    "?ends_before=2026-04-26T23%3A59%3A59Z"
    "&starts_after=2026-03-27T00%3A00%3A00Z"
    "&include_canceled=true&expand=true"
)


WAITLISTED_BOOKING_ID = "a1e2f3d4-5678-4abc-9def-0123456789ab"
_A_DATE = "2026-03-27T08:00:00"

# A member stops reading its dates once it is added to BookingStatus, so each one needs a deliberate state here.
EXPECTED_STATE_BY_MEMBER = {
    BookingStatus.Pending: "active",
    BookingStatus.Requested: "active",
    BookingStatus.Booked: "active",
    BookingStatus.Cancelled: "cancelled",
    BookingStatus.LateCancelled: "active",
    BookingStatus.Waitlisted: "active",
    BookingStatus.CheckedIn: "checked_in",
    BookingStatus.CheckinPending: "active",
    BookingStatus.CheckinRequested: "active",
    BookingStatus.Confirmed: "active",
    BookingStatus.CheckinCancelled: "active",
    BookingStatus.CancelCheckinPending: "active",
    BookingStatus.CancelCheckinRequested: "active",
}


def make_booking(status: str, cancelled: str | None = None, checked_in: str | None = None) -> Booking:
    """Builds a v1 booking from the first fixture record, with the status and date fields under test."""
    raw = load_fixture("bookings/get_bookings")["data"][0]
    raw["class"]["studio"] = {"studioUUId": "studio-uuid"}
    return Booking.model_validate(raw | {"status": status, "cancelledDate": cancelled, "checkedInDate": checked_in})


def test_get_bookings(mock_otf) -> None:
    result = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(b, Booking) for b in result)

    first = result[0]
    assert isinstance(first.booking_uuid, str)
    assert first.booking_uuid != ""
    assert first.otf_class is not None
    assert isinstance(first.otf_class.class_uuid, str)


def test_get_bookings_new(mock_otf) -> None:
    # dates must match fixture get_bookings_new__2026-03-27.json URL params exactly
    result = mock_otf.bookings.get_bookings_new(
        start_date=date(2026, 3, 27),
        end_date=date(2026, 4, 26),
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(b, BookingV2) for b in result)

    first = result[0]
    assert isinstance(first.booking_id, str)
    assert first.booking_id != ""


def test_get_bookings_new_by_date(mock_otf, mock_router) -> None:
    # get_bookings_new_by_date sends include_canceled=true, but captured fixtures
    # only have include_canceled=false. Register the true variant with the same data.
    fixture_data = load_fixture(f"bookings/get_bookings_new__{_BOOKINGS_NEW_DATE_PARAMS}")
    mock_router.request("GET", _BOOKINGS_NEW_URL).mock(
        return_value=httpx.Response(200, json=fixture_data)
    )

    result = mock_otf.bookings.get_bookings_new_by_date(
        start_date=date(2026, 3, 27),
        end_date=date(2026, 4, 26),
    )

    assert isinstance(result, dict)
    assert len(result) > 0

    first_key = next(iter(result))
    assert isinstance(first_key, datetime)
    assert isinstance(result[first_key], BookingV2)


def test_get_classes(mock_otf) -> None:
    result = mock_otf.bookings.get_classes()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(c, OtfClass) for c in result)

    first = result[0]
    assert isinstance(first.class_uuid, str)
    assert first.class_uuid != ""
    assert isinstance(first.name, str)
    assert first.studio is not None
    assert isinstance(first.studio.studio_uuid, str)


@pytest.mark.parametrize("class_type", ["HYROX_60", "OPEN_STUDIO"])
def test_get_classes_keeps_new_class_types(mock_otf, mock_router, class_type: str) -> None:
    """Classes whose type is HYROX_60 or OPEN_STUDIO are returned, not dropped (#147)."""
    target_uuid = mock_otf.bookings.get_classes()[0].class_uuid

    fixture_data = load_fixture("bookings/get_classes")
    for item in fixture_data["items"]:
        if item["ot_base_class_uuid"] == target_uuid:
            item["type"] = class_type
    mock_router.request("GET", _CLASSES_URL).mock(return_value=httpx.Response(200, json=fixture_data))

    matching = [c for c in mock_otf.bookings.get_classes() if c.class_uuid == target_uuid]

    assert len(matching) == 1
    assert matching[0].class_type == class_type


@pytest.mark.parametrize("class_type", ["HYROX_60", "OPEN_STUDIO"])
def test_get_end_time_new_class_types_last_60_minutes(class_type: str) -> None:
    start = datetime(2026, 3, 27, 9, 0)

    end = get_end_time(start, ClassType(class_type))

    assert (end - pendulum.instance(start)).total_seconds() == 3600


@pytest.mark.parametrize(
    ["class_type", "minutes"],
    [
        ("HYROX_75", 75),
        ("HYROX_30", 30),
        ("HYROX_120", 120),
        ("HYROX_29", 60),
        ("HYROX_121", 60),
        ("CLASS_2", 60),
        ("OPEN_STUDIO_24", 60),
        ("TREAD_50_V2", 60),
        ("BRAND_NEW", 60),
        ("OTHER", 60),
        ("ORANGE_90", 90),
        ("STRENGTH_50", 50),
    ],
)
def test_get_end_time_by_class_type(class_type: str, minutes: int) -> None:
    start = datetime(2026, 3, 27, 9, 0)

    end = get_end_time(start, class_type)

    assert (end - pendulum.instance(start)).total_seconds() == minutes * 60


@pytest.mark.parametrize("model", [OtfClass, BookingV2Class])
def test_unrecognized_class_type_keeps_raw_value(model: type) -> None:
    raw = {
        "id": "class-id",
        "ot_base_class_uuid": "class-uuid",
        "name": "A class",
        "type": "HYROX_75",
        "ends_at_local": "2026-03-27T10:15:00",
        "starts_at_local": "2026-03-27T09:00:00",
        "studio": {"studioUUId": "studio-uuid"} if model is OtfClass else None,
    }

    result = model.model_validate(raw)

    assert result.class_type == "HYROX_75"
    assert not isinstance(result.class_type, ClassType)
    assert result.model_dump(mode="json")["class_type"] == "HYROX_75"


def test_get_classes_keeps_unrecognized_class_type_and_filters_to_it(mock_otf, mock_router) -> None:
    target_uuid = mock_otf.bookings.get_classes()[0].class_uuid

    fixture_data = load_fixture("bookings/get_classes")
    for item in fixture_data["items"]:
        if item["ot_base_class_uuid"] == target_uuid:
            item["type"] = "HYROX_75"
    mock_router.request("GET", _CLASSES_URL).mock(return_value=httpx.Response(200, json=fixture_data))

    result = mock_otf.bookings.get_classes(filters=ClassFilter(class_type="hyrox 75"))

    assert {c.class_uuid for c in result} == {target_uuid}
    assert result[0].class_type == "HYROX_75"


def test_near_miss_spelling_is_a_raw_value_not_a_member() -> None:
    # the member is "Late Cancelled"; only the case of one letter differs
    assert not isinstance(make_booking("Late cancelled").status, BookingStatus)


def test_booking_str_handles_unrecognized_status() -> None:
    assert "(No Show)" in str(make_booking("No Show"))


@pytest.mark.parametrize(
    ["status", "cancelled", "checked_in", "state"],
    [
        ("Cancelled", None, None, "cancelled"),
        ("Checked In", None, None, "checked_in"),
        ("Booked", None, None, "active"),
        # known statuses never read the dates
        ("Booked", _A_DATE, _A_DATE, "active"),
        ("Late Cancelled", _A_DATE, None, "active"),
        ("Cancelled", None, _A_DATE, "cancelled"),
        # unrecognized statuses read only the dates
        ("No Show", None, None, "active"),
        ("No Show", _A_DATE, None, "cancelled"),
        ("No Show", None, _A_DATE, "checked_in"),
        ("No Show", _A_DATE, _A_DATE, "cancelled"),
    ],
)
def test_booking_state(status: str, cancelled: str | None, checked_in: str | None, state: str) -> None:
    assert make_booking(status, cancelled, checked_in).state == state


@pytest.mark.parametrize("status", list(BookingStatus))
def test_every_booking_status_member_has_a_decided_state(status: BookingStatus) -> None:
    # both dates are set to show that a member's state comes from the map, not from its dates
    booking = make_booking(status.value, _A_DATE, _A_DATE)

    assert booking.state == EXPECTED_STATE_BY_MEMBER[status]


@pytest.mark.parametrize(
    ["cancelled", "checked_in", "books"],
    [(_A_DATE, None, True), (None, None, False), (None, _A_DATE, False)],
)
def test_book_class_with_unrecognized_existing_status_acts_on_its_dates(
    mock_otf, cancelled: str | None, checked_in: str | None, books: bool
) -> None:
    existing = make_booking("No Show", cancelled, checked_in)
    saved = {"savedBookings": [{"classBookingUUId": existing.booking_uuid}]}

    with (
        patch.object(mock_otf.bookings, "get_booking_from_class", return_value=existing),
        patch.object(mock_otf.bookings, "get_booking", return_value=existing),
        patch.object(mock_otf.bookings.client, "put_class", return_value=saved) as put_class,
    ):
        if books:
            mock_otf.bookings.book_class("class-uuid")
        else:
            with pytest.raises(AlreadyBookedError):
                mock_otf.bookings.book_class("class-uuid")

    assert put_class.called is books


def test_already_booked_error_names_the_status(mock_otf) -> None:
    existing = make_booking("No Show")

    with (
        patch.object(mock_otf.bookings, "get_booking_from_class", return_value=existing),
        pytest.raises(AlreadyBookedError, match="No Show"),
    ):
        mock_otf.bookings.book_class("class-uuid")


@pytest.mark.parametrize(["cancelled", "books"], [(_A_DATE, True), (None, False)])
def test_book_class_conflict_check_acts_on_an_unrecognized_status(mock_otf, cancelled: str | None, books: bool) -> None:
    record = load_fixture("bookings/get_bookings")["data"][0] | {
        "status": "No Show",
        "cancelledDate": cancelled,
        "checkedInDate": None,
    }
    # same time window as the existing booking, so only its state decides whether this conflicts
    overlapping = OtfClass.model_validate(
        {
            "ot_base_class_uuid": "another-class-uuid",
            "name": "An overlapping class",
            "type": "ORANGE_60",
            "starts_at_local": record["class"]["startDateTime"],
            "ends_at_local": record["class"]["endDateTime"],
            "studio": {"studioUUId": "studio-uuid"},
        }
    )
    saved = {"savedBookings": [{"classBookingUUId": "new-booking-uuid"}]}

    with (
        patch.object(mock_otf.bookings, "get_booking_from_class", side_effect=ResourceNotFoundError("none")),
        patch.object(mock_otf.bookings, "get_booking", return_value=make_booking("Booked")),
        patch.object(mock_otf.bookings.client, "get_bookings", return_value=[record]),
        patch.object(mock_otf.bookings.client, "put_class", return_value=saved) as put_class,
    ):
        if books:
            mock_otf.bookings.book_class(overlapping)
        else:
            with pytest.raises(ConflictingBookingError):
                mock_otf.bookings.book_class(overlapping)

    assert put_class.called is books


@pytest.mark.parametrize(
    ["kwargs", "kept"],
    [
        ({}, {"active"}),
        ({"exclude_cancelled": False}, {"active", "cancelled"}),
        ({"exclude_checkedin": False}, {"active", "checked_in"}),
    ],
)
def test_get_bookings_exclusions_apply_to_unrecognized_statuses(mock_otf, kwargs, kept) -> None:
    dates = {"active": (None, None), "cancelled": (_A_DATE, None), "checked_in": (None, _A_DATE)}
    resp = [
        load_fixture("bookings/get_bookings")["data"][0]
        | {"classBookingUUId": name, "status": "No Show", "cancelledDate": cancelled, "checkedInDate": checked_in}
        for name, (cancelled, checked_in) in dates.items()
    ]

    with patch.object(mock_otf.bookings.client, "get_bookings", return_value=resp):
        result = mock_otf.bookings.get_bookings(**kwargs)

    assert {b.booking_uuid for b in result} == kept


@pytest.mark.parametrize(
    ["status", "sent"],
    [
        ("No Show", "No Show"),
        (BookingStatus.Booked, "Booked"),
        ([BookingStatus.Booked, "No Show"], "Booked,No Show"),
    ],
)
def test_get_bookings_sends_a_status_read_from_a_response(mock_otf, status, sent: str) -> None:
    with patch.object(mock_otf.bookings.client, "get_bookings", return_value=[]) as get_bookings:
        mock_otf.bookings.get_bookings(status=status)

    get_bookings.assert_called_once_with(None, None, sent)


def test_unrecognized_value_warns_once_per_vocabulary_and_value() -> None:
    reported_values.clear()

    with patch("otf_api.models.vocabulary.LOGGER.warning") as warning:
        make_booking("No Show")
        make_booking("No Show")
        assert warning.call_count == 1

        make_booking("Ghosted")
        assert warning.call_count == 2

        make_booking("Booked")
        assert warning.call_count == 2

        StudioDetail.model_validate({"studioUUId": "uuid", "studioStatus": "No Show"})
        assert warning.call_count == 3


def test_value_of_the_wrong_type_still_fails_the_record_and_is_not_reported() -> None:
    with patch("otf_api.models.vocabulary.LOGGER.warning") as warning, pytest.raises(ValidationError):
        make_booking(123)  # pyright: ignore[reportArgumentType]

    warning.assert_not_called()


@pytest.mark.parametrize(
    ["model", "field", "members", "primitive"],
    [
        (OtfClass, "class_type", ClassType, "string"),
        (BookingV2Class, "class_type", ClassType, "string"),
        (Booking, "status", BookingStatus, "string"),
        (StudioDetail, "status", StudioStatus, "string"),
        (FitnessBenchmark, "equipment_id", EquipmentType, "integer"),
    ],
)
def test_schema_publishes_known_values_and_open_primitive(model, field, members, primitive) -> None:
    schema = model.model_json_schema(by_alias=False)

    branches = schema["properties"][field]["anyOf"]
    enum_ref = next(b["$ref"] for b in branches if "$ref" in b).removeprefix("#/$defs/")

    assert {"type": primitive} in branches
    assert schema["$defs"][enum_ref]["enum"] == [m.value for m in members]


def test_get_bookings_with_default_filters(mock_otf) -> None:
    all_bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
    filtered = mock_otf.bookings.get_bookings()

    assert isinstance(filtered, list)
    assert len(filtered) > 0
    assert len(filtered) <= len(all_bookings)


def test_get_booking_from_class(mock_otf) -> None:
    bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
    assert len(bookings) > 0

    target = bookings[0]
    result = mock_otf.bookings.get_booking_from_class(target.otf_class.class_uuid)

    assert isinstance(result, Booking)
    assert result.booking_uuid == target.booking_uuid


def test_get_class_from_booking(mock_otf) -> None:
    bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
    booked = [b for b in bookings if b.otf_class.class_uuid]
    assert len(booked) > 0

    result = mock_otf.bookings.get_class_from_booking(booked[0])

    assert isinstance(result, OtfClass)
    assert result.class_uuid == booked[0].otf_class.class_uuid


# get_class_from_booking_new / get_booking_from_class_new cannot be tested:
# the new booking class IDs (from get_bookings_new fixtures) don't overlap with
# any class IDs in the get_classes fixture, so the lookup always fails.


def test_waitlisted_booking_returns_waitlisted_status(mock_otf) -> None:
    result = mock_otf.bookings.get_bookings_new(
        start_date=date(2026, 3, 27),
        end_date=date(2026, 4, 26),
    )

    waitlisted = [b for b in result if b.booking_id == WAITLISTED_BOOKING_ID]
    assert len(waitlisted) == 1

    booking = waitlisted[0]
    assert booking.waitlist_position == 3
    assert booking.status == BookingStatus.Waitlisted


def test_non_waitlisted_booking_never_returns_waitlisted(mock_otf) -> None:
    result = mock_otf.bookings.get_bookings_new(
        start_date=date(2026, 3, 27),
        end_date=date(2026, 4, 26),
    )

    non_waitlisted = [b for b in result if b.waitlist_position is None]
    assert len(non_waitlisted) > 0

    for booking in non_waitlisted:
        assert booking.waitlist_position is None
        assert booking.status != BookingStatus.Waitlisted
