"""Tests for bug fixes #121 and #122."""

from datetime import date
from unittest.mock import patch

import httpx
import pytest
from conftest import MOCK_MEMBER_UUID

from otf_api.models.bookings import Booking, BookingV2


def test_cancel_booking_rejects_booking_v2(mock_otf, mock_router) -> None:
    """cancel_booking(BookingV2) should raise TypeError."""
    bookings = mock_otf.bookings.get_bookings_new(start_date=date(2026, 3, 27), end_date=date(2026, 4, 26))
    booking_v2 = bookings[0]
    assert isinstance(booking_v2, BookingV2)

    with pytest.raises(TypeError):
        mock_otf.bookings.cancel_booking(booking_v2)


def test_cancel_booking_new_rejects_booking_v1(mock_otf, mock_router) -> None:
    """cancel_booking_new(Booking) should raise TypeError."""
    bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
    booking_v1 = bookings[0]
    assert isinstance(booking_v1, Booking)

    with pytest.raises(TypeError):
        mock_otf.bookings.cancel_booking_new(booking_v1)


def test_cancel_booking_with_booking_object(mock_otf, mock_router) -> None:
    """cancel_booking(Booking) should call the v1 delete endpoint."""
    bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
    booking_v1 = bookings[0]

    delete_url = (
        f"https://api.orangetheory.co/member/members/{MOCK_MEMBER_UUID}"
        f"/bookings/{booking_v1.booking_uuid}?confirmed=true"
    )
    delete_route = mock_router.request("DELETE", delete_url).mock(return_value=httpx.Response(200, json={}))

    mock_otf.bookings.cancel_booking(booking_v1)
    assert delete_route.called


def test_cancel_booking_new_with_booking_v2_object(mock_otf, mock_router) -> None:
    """cancel_booking_new(BookingV2) should call the v2 delete endpoint."""
    bookings = mock_otf.bookings.get_bookings_new(start_date=date(2026, 3, 27), end_date=date(2026, 4, 26))
    booking_v2 = bookings[0]

    delete_url = f"https://api.orangetheory.io/v1/bookings/me/{booking_v2.booking_id}"
    delete_route = mock_router.request("DELETE", delete_url).mock(return_value=httpx.Response(200, json={}))

    mock_otf.bookings.cancel_booking_new(booking_v2)
    assert delete_route.called


def test_workout_from_booking_has_class_uuid(mock_otf) -> None:
    """Bug #122: Workouts from get_workout_from_booking should have class_uuid populated."""
    bookings = mock_otf.bookings.get_bookings_new(start_date=date(2026, 3, 27), end_date=date(2026, 4, 26))
    booking_with_workout = next(b for b in bookings if b.workout and b.workout.performance_summary_id)
    expected_class_uuid = booking_with_workout.otf_class.class_uuid
    assert expected_class_uuid is not None

    with patch.object(mock_otf.bookings, "get_booking_new") as mock_get:
        workout = mock_otf.workouts.get_workout_from_booking(booking_with_workout)

    mock_get.assert_not_called()
    assert workout.class_uuid == expected_class_uuid
