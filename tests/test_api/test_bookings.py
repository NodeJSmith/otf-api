"""Tests for BookingApi read-only methods."""

from datetime import date

from otf_api.models.bookings import Booking, BookingV2, OtfClass


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


# get_bookings_new_by_date cannot be tested: it hardcodes exclude_cancelled=False
# (include_canceled=true in the HTTP request), but all captured fixtures used
# include_canceled=false. A fixture with include_canceled=true would be needed.


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
