from datetime import time

from otf_api import Otf
from otf_api.filters import ClassFilter, ClassType, DoW


def main():
    otf = Otf()

    # you can use the ClassFilter model to setup filters to only return the classes
    # you care about. All attributes set on a filter have to be true - but all attributes
    # that accept a list can have multiple values that will be OR'd together.

    # For example, the following filter will return all classes that are on a Tuesday or Thursday
    # that start at 9:45 and are either a 60 or 90 minute 2G/3G class

    cf = ClassFilter(
        day_of_week=[DoW.TUESDAY, DoW.THURSDAY],
        start_time=time(9, 45),
        class_type=ClassType.get_standard_class_types(),
    )

    # this filter will return all classes that are on a Saturday that start at 10:30 and are a 50 minute Tread class
    cf2 = ClassFilter(day_of_week=DoW.SATURDAY, start_time=time(10, 30), class_type=ClassType.TREAD_50)

    # the call to `get_classes` will return classes that match either of these filters

    classes = otf.get_classes(filters=[cf, cf2])
    print(classes[0].model_dump_json(indent=4))

    """
    {
        "class_uuid": "c465a372-5cda-4e4b-addd-e695db2c4efa",
        "name": "Orange 60 Min 2G",
        "class_type": "ORANGE_60",
        "coach": "Coach",
        "ends_at": "2025-01-23T10:45:00",
        "starts_at": "2025-01-23T09:45:00",
        "studio": {
            "studio_uuid": "c9e81931-6845-4ab5-ba06-6479d63553ae",
            "contact_email": "studioemailaddressexample@orangetheoryfitness.com",
            "distance": 0.0,
            "location": {
                "address_line1": "2835 N Sandbank Rd.",
                "address_line2": null,
                "city": "AnyTown",
                "postal_code": "11111",
                "state": "OH",
                "country": "United States",
                "phone_number": "1234567890",
                "latitude": 92.73407745,
                "longitude": 3.46269226
            },
            "name": "AnyTown OH - East",
            "status": "Active",
            "time_zone": "America/NewYork"
        },
        "booking_capacity": 24,
        "full": false,
        "max_capacity": 24,
        "waitlist_available": false,
        "waitlist_size": 0,
        "is_booked": true,
        "is_cancelled": false,
        "is_home_studio": true
    }

    """

    # You can also get the classes that you have booked
    # You can pass a start_date, end_date, status, and limit as arguments

    bookings = otf.get_bookings()

    print("Latest Upcoming Class:")
    print(bookings[-1].model_dump_json(indent=4))

    """
    {
        "booking_uuid": "946e45c0-89a6-4061-a730-2ead6d5ec1b6",
        "is_intro": false,
        "status": "Booked",
        "booked_date": "2025-01-20T06:02:51Z",
        "checked_in_date": null,
        "cancelled_date": null,
        "created_date": "2025-01-20T06:02:51Z",
        "updated_date": "2025-01-20T06:02:53Z",
        "is_deleted": false,
        "waitlist_position": null,
        "otf_class": {
            "class_uuid": "3b7158c2-e80c-4053-9e5f-f156e5660059",
            "name": "Tread 50",
            "starts_at": "2025-02-18T10:00:00",
            "ends_at": "2025-02-18T10:50:00",
            "is_available": true,
            "is_cancelled": false,
            "studio": {
            "studio_uuid": "c9e81931-6845-4ab5-ba06-6479d63553ae",
            "contact_email": "studioemailaddressexample@orangetheoryfitness.com",
            "distance": 0.0,
            "location": {
                "address_line1": "2835 N Sandbank Rd.",
                "address_line2": null,
                "city": "AnyTown",
                "postal_code": "11111",
                "state": "OH",
                "country": "United States",
                "phone_number": "1234567890",
                "latitude": 92.73407745,
                "longitude": 3.46269226
            },
            "name": "AnyTown OH - East",
            "status": "Active",
            "time_zone": "America/NewYork"
            },
            "coach": {
                "coach_uuid": "74cac280-f7d3-4fea-a7b6-e59dc2fd3bca",
                "first_name": "Coach",
                "last_name": "Coach"
            }
        },
        "is_home_studio": true
    }
    """


if __name__ == "__main__":
    main()
