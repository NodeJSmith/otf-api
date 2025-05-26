from datetime import datetime
from typing import Any

import pendulum

from otf_api.api.client import API_IO_BASE_URL, OtfClient


class BookingClient:
    """Client for managing bookings and classes in the OTF API.

    This class provides methods to retrieve classes, book classes, cancel bookings, and rate classes.
    """

    def __init__(self, client: OtfClient):
        self.client = client
        self.member_uuid = client.member_uuid

    def classes_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:  # noqa: ANN401
        """Perform an API request to the classes API."""
        return self.client.do(method, API_IO_BASE_URL, path, params, headers=headers, **kwargs)

    def get_classes(self, studio_uuids: list[str]) -> dict:
        """Retrieve raw class data."""
        return self.classes_request("GET", "/v1/classes", params={"studio_ids": studio_uuids})["items"]

    def delete_booking(self, booking_uuid: str) -> dict:
        """Cancel a booking by booking_uuid."""
        resp = self.client.default_request(
            "DELETE", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}", params={"confirmed": "true"}
        )

        return resp

    def put_class(self, body: dict) -> dict:
        """Book a class by class_uuid.

        Args:
            body (dict): The request body containing booking details.

        Returns:
            dict: The response from the booking request.

        Raises:
            AlreadyBookedError: If the class is already booked.
            OutsideSchedulingWindowError: If the class is outside the scheduling window.
            OtfException: If there is an error booking the class.
        """
        return self.client.default_request("PUT", f"/member/members/{self.member_uuid}/bookings", json=body)["data"]

    def post_class_new(self, body: dict[str, str | bool]) -> dict:
        """Book a class by class_id."""
        return self.classes_request("POST", "/v1/bookings/me", json=body)

    def get_booking(self, booking_uuid: str) -> dict:
        """Retrieve raw booking data."""
        return self.client.default_request("GET", f"/member/members/{self.member_uuid}/bookings/{booking_uuid}")["data"]

    def get_bookings(self, start_date: str | None, end_date: str | None, status: str | list[str] | None) -> dict:
        """Retrieve raw bookings data."""
        if isinstance(status, list):
            status = ",".join(status)

        return self.client.default_request(
            "GET",
            f"/member/members/{self.member_uuid}/bookings",
            params={"startDate": start_date, "endDate": end_date, "statuses": status},
        )["data"]

    def get_bookings_new(
        self,
        ends_before: datetime,
        starts_after: datetime,
        include_canceled: bool = True,
        expand: bool = False,
    ) -> dict:
        """Retrieve raw bookings data."""
        params: dict[str, bool | str] = {
            "ends_before": pendulum.instance(ends_before).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "starts_after": pendulum.instance(starts_after).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        params["include_canceled"] = include_canceled if include_canceled is not None else True
        params["expand"] = expand if expand is not None else False

        return self.classes_request("GET", "/v1/bookings/me", params=params)["items"]

    def delete_booking_new(self, booking_id: str) -> None:
        """Cancel a booking by booking_id."""
        self.classes_request("DELETE", f"/v1/bookings/me/{booking_id}")

    def post_class_rating(
        self, class_uuid: str, performance_summary_id: str, class_rating: int, coach_rating: int
    ) -> dict:
        """Retrieve raw response from rating a class and coach."""
        return self.client.default_request(
            "POST",
            "/mobile/v1/members/classes/ratings",
            json={
                "classUUId": class_uuid,
                "otBeatClassHistoryUUId": performance_summary_id,
                "classRating": class_rating,
                "coachRating": coach_rating,
            },
        )
