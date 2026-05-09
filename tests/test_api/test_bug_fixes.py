"""Tests for bug fixes #121 and #122."""

from datetime import date
from unittest.mock import patch

import httpx
from conftest import MOCK_MEMBER_UUID

from otf_api.models.bookings import Booking, BookingV2


class TestCancelBookingCrossDispatch:
    """Bug #121: cancel methods missing return after cross-dispatch."""

    def test_cancel_booking_with_v2_does_not_fall_through(self, mock_otf, mock_router) -> None:
        """cancel_booking(BookingV2) should dispatch to cancel_booking_new and return."""
        bookings = mock_otf.bookings.get_bookings_new(
            start_date=date(2026, 3, 27), end_date=date(2026, 4, 26)
        )
        booking_v2 = bookings[0]
        assert isinstance(booking_v2, BookingV2)

        delete_url = f"https://api.orangetheory.io/v1/bookings/me/{booking_v2.booking_id}"
        delete_route = mock_router.request("DELETE", delete_url).mock(return_value=httpx.Response(200, json={}))

        mock_otf.bookings.cancel_booking(booking_v2)

        assert delete_route.called

    def test_cancel_booking_new_with_v1_does_not_fall_through(self, mock_otf, mock_router) -> None:
        """cancel_booking_new(Booking) should dispatch to cancel_booking and return."""
        bookings = mock_otf.bookings.get_bookings(exclude_cancelled=False, exclude_checkedin=False)
        booking_v1 = bookings[0]
        assert isinstance(booking_v1, Booking)

        delete_url = (
            f"https://api.orangetheory.co/member/members/{MOCK_MEMBER_UUID}"
            f"/bookings/{booking_v1.booking_uuid}?confirmed=true"
        )
        delete_route = mock_router.request("DELETE", delete_url).mock(return_value=httpx.Response(200, json={}))

        mock_otf.bookings.cancel_booking_new(booking_v1)

        assert delete_route.called


class TestGetWorkoutFromBookingClassUuid:
    """Bug #122: get_workout_from_booking produces workouts with class_uuid=None."""

    def test_workout_from_booking_has_class_uuid(self, mock_otf) -> None:
        """Workouts from get_workout_from_booking should have class_uuid populated."""
        bookings = mock_otf.bookings.get_bookings_new(
            start_date=date(2026, 3, 27), end_date=date(2026, 4, 26)
        )
        booking_with_workout = next(b for b in bookings if b.workout and b.workout.performance_summary_id)
        expected_class_uuid = booking_with_workout.otf_class.class_uuid
        assert expected_class_uuid is not None

        with patch.object(mock_otf.bookings, "get_booking_new", return_value=booking_with_workout):
            workout = mock_otf.workouts.get_workout_from_booking(booking_with_workout)

        assert workout.class_uuid == expected_class_uuid
