"""Tests for BookingApi read-only methods."""

from datetime import date, datetime

import httpx
import respx
from conftest import load_fixture

from otf_api.models.bookings import Booking, BookingV2, OtfClass

_BOOKINGS_NEW_DATE_PARAMS = "2026-03-27"
_BOOKINGS_NEW_URL = (
    "https://api.orangetheory.io/v1/bookings/me"
    "?ends_before=2026-04-26T23%3A59%3A59Z"
    "&starts_after=2026-03-27T00%3A00%3A00Z"
    "&include_canceled=true&expand=true"
)


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
