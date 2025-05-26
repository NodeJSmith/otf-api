from datetime import time

import pendulum

from otf_api import Otf
from otf_api.filters import ClassFilter, ClassType, DoW


def main():  # noqa: D103, ANN201
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

    classes = otf.bookings.get_classes(filters=[cf, cf2])
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

    bookings = otf.bookings.get_bookings()

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

    # There is a new bookings endpoint that will return a list of bookings
    # both future bookings and past workouts, ordered by the start time of the class
    # You can pass a start and end date, as well as if you want to include canceled bookings
    # If it is a past class that you attended, it will also include workout data - it is best
    # to use the `get_workout_from_boooking` method to get an actual Workout object, as this
    # combines data from multiple endpoints to give you the same data that is shown in the app
    bookings_new = otf.bookings.get_bookings_new()
    print("Furthest Upcoming Class (New):")
    print(bookings_new[0].model_dump_json(indent=4))
    """
    {
        "booking_id": "94644114-8ab7-42b9-8e1a-df42fbafb3f0",
        "member_uuid": "c07571f5-b06e-42f8-90ab-a549293be7f2",
        "service_name": null,
        "cross_regional": false,
        "intro": false,
        "checked_in": false,
        "canceled": false,
        "late_canceled": false,
        "canceled_at": null,
        "ratable": false,
        "otf_class": {
            "class_id": "2ad39896-7fdc-44bf-b979-d53ffc6108a3",
            "name": "Orange 60 Min 2G",
            "class_type": "ORANGE_60",
            "starts_at": "2025-06-08T09:30:00",
            "studio": {
                "phone_number": "1234567890",
                "latitude": 92.73407745,
                "longitude": 3.46269226
                "studio_uuid": "00718673-8486-4e16-a861-548ead1e2e8b",
                "name": "AnyTown OH - East",
                "time_zone": "America/Chicago",
                "email": "studiomanager0590@orangetheoryfitness.com",
                "address": {
                    "address_line1": "2835 N Sandbank Rd.",
                    "city": "AnyTown",
                    "postal_code": "11111",
                    "state": "KS",
                    "country": "United States"
                }
            },
            "coach": "Machaela"
        },
        "workout": null,
        "coach_rating": null,
        "class_rating": null,
        "paying_studio_id": "32cafa6f-a1f9-4e34-92ce-a4f34d87892c",
        "mbo_booking_id": "094263",
        "mbo_unique_id": "464010101",
        "mbo_paying_unique_id": "464010101",
        "person_id": "e14f217c-d469-4182-857f-7249392f5191"
    }
    """

    # you can get the workout data from a booking by calling `get_workout_from_booking`
    bookings_new = otf.bookings.get_bookings_new(pendulum.today().subtract(months=1))
    booking = next(x for x in bookings_new if x.workout is not None)
    workout = otf.workouts.get_workout_from_booking(booking)
    print(workout.model_dump_json(indent=4, exclude_none=True))
    """
    {
        "performance_summary_id": "0897997f-3894-49c1-8cad-df50da253829",
        "class_history_uuid": "0897997f-3894-49c1-8cad-df50da253829",
        "booking_id": "91d2866e-e9ba-4ff6-be8f-32ca5a06ecab",
        "class_uuid": "808e8bfe-aacb-4f07-9eb5-00863225ab2d",
        "coach": "Machaela",
        "ratable": false,
        "calories_burned": 421,
        "splat_points": 4,
        "step_count": 4175,
        "zone_time_minutes": {
            "gray": 7,
            "blue": 18,
            "green": 27,
            "orange": 4,
            "red": 0
        },
        "heart_rate": {
            "max_hr": 191,
            "peak_hr": 166,
            "peak_hr_percent": 87,
            "avg_hr": 137,
            "avg_hr_percent": 72
        },
        "active_time_seconds": 3333,
        "rower_data": {
            "avg_pace": {
                "display_value": "00:01:43",
                "display_unit": "min/500m",
                "metric_value": 103.0
            },
            "avg_speed": {
                "display_value": 17.7,
                "display_unit": "km/h",
                "metric_value": 17.7
            },
            "max_pace": {
                "display_value": "00:01:33",
                "display_unit": "min/500m",
                "metric_value": 93.0
            },
            "max_speed": {
                "display_value": 19.3,
                "display_unit": "km/h",
                "metric_value": 19.3
            },
            "moving_time": {
                "display_value": "00:02:13",
                "display_unit": "Duration",
                "metric_value": 133.0
            },
            "total_distance": {
                "display_value": 469.0,
                "display_unit": "m",
                "metric_value": 469.0
            },
            "avg_cadence": {
                "display_value": 28.6,
                "display_unit": "",
                "metric_value": 28.6
            },
            "avg_power": {
                "display_value": 241.1,
                "display_unit": "watt",
                "metric_value": 241.1
            },
            "max_cadence": {
                "display_value": 32.0,
                "display_unit": "",
                "metric_value": 32.0
            }
        },
        "treadmill_data": {
            "avg_pace": {
                "display_value": "00:15:00",
                "display_unit": "min/mile",
                "metric_value": 900.0
            },
            "avg_speed": {
                "display_value": 4.0,
                "display_unit": "mph",
                "metric_value": 4.0
            },
            "max_pace": {
                "display_value": "00:08:34",
                "display_unit": "min/mile",
                "metric_value": 514.0
            },
            "max_speed": {
                "display_value": 7.0,
                "display_unit": "mph",
                "metric_value": 7.0
            },
            "moving_time": {
                "display_value": "00:24:56",
                "display_unit": "Duration",
                "metric_value": 1496.0
            },
            "total_distance": {
                "display_value": 1.93,
                "display_unit": "miles",
                "metric_value": 1.93
            },
            "avg_incline": {
                "display_value": 1.6,
                "display_unit": "%",
                "metric_value": 1.6
            },
            "elevation_gained": {
                "display_value": 160.353,
                "display_unit": "feet",
                "metric_value": 160.353
            },
            "max_incline": {
                "display_value": 12.0,
                "display_unit": "%",
                "metric_value": 12.0
            }
        },
        "class_rating": {
            "id": "21",
            "description": "Double Thumbs Up",
            "value": 3
        },
        "coach_rating": {
            "id": "18",
            "description": "Double Thumbs Up",
            "value": 3
        },
        "otf_class": {
            "class_id": "26f527d8-d0c9-4977-bc5e-b2e18d5f3136",
            "name": "Orange 60 Min 2G",
            "class_type": "ORANGE_60",
            "starts_at": "2025-05-11T09:30:00",
            "studio": {
                "latitude": 92.73407745,
                "longitude": 3.46269226
                "studio_uuid": "00718673-8486-4e16-a861-548ead1e2e8b",
                "name": "AnyTown OH - East",
                "time_zone": "America/Chicago",
                "email": "studiomanager0590@orangetheoryfitness.com",
                "address": {
                    "address_line1": "2835 N Sandbank Rd.",
                    "city": "AnyTown",
                    "postal_code": "11111",
                    "state": "KS",
                    "country": "United States"
                }
            },
            "coach": "Machaela"
        },
        "studio": {
            "latitude": 92.73407745,
            "longitude": 3.46269226
            "studio_uuid": "00718673-8486-4e16-a861-548ead1e2e8b",
            "name": "AnyTown OH - East",
            "time_zone": "America/Chicago",
            "email": "studiomanager0590@orangetheoryfitness.com",
            "address": {
                "address_line1": "2835 N Sandbank Rd.",
                "city": "AnyTown",
                "postal_code": "11111",
                "state": "KS",
                "country": "United States"
            }
        },
        "telemetry": {
            "member_uuid": "10df3694-675b-45c2-9244-1fa6ec2ee47e",
            "performance_summary_id": "0897997f-3894-49c1-8cad-df50da253829",
            "class_history_uuid": "0897997f-3894-49c1-8cad-df50da253829",
            "class_start_time": "2025-05-11T14:31:36Z",
            "max_hr": 191,
            "zones": {
                "gray": {
                    "start_bpm": 96,
                    "end_bpm": 116
                },
                "blue": {
                    "start_bpm": 117,
                    "end_bpm": 135
                },
                "green": {
                    "start_bpm": 136,
                    "end_bpm": 159
                },
                "orange": {
                    "start_bpm": 160,
                    "end_bpm": 175
                },
                "red": {
                    "start_bpm": 176,
                    "end_bpm": 191
                }
            },
            "window_size": 23,
            "telemetry": [
                {
                    "relative_timestamp": 0,
                    "agg_splats": 0,
                    "agg_calories": 0,
                    "timestamp": "2025-05-11T14:31:36Z"
                },
                {
                    "relative_timestamp": 23,
                    "hr": 111,
                    "agg_splats": 0,
                    "agg_calories": 1,
                    "timestamp": "2025-05-11T14:31:59Z",
                    "tread_data": {
                        "tread_speed": 1.34,
                        "tread_incline": 1.0,
                        "agg_tread_distance": 6
                    }
                },
                {
                    "relative_timestamp": 46,
                    "hr": 112,
                    "agg_splats": 0,
                    "agg_calories": 3,
                    "timestamp": "2025-05-11T14:32:22Z",
                    "tread_data": {
                        "tread_speed": 2.24,
                        "tread_incline": 1.0,
                        "agg_tread_distance": 52
                    }
                },
                {
                    "relative_timestamp": 69,
                    "hr": 125,
                    "agg_splats": 0,
                    "agg_calories": 5,
                    "timestamp": "2025-05-11T14:32:45Z",
                    "tread_data": {
                        "tread_speed": 2.24,
                        "tread_incline": 1.0,
                        "agg_tread_distance": 100
                    }
                },
                {
                    "relative_timestamp": 92,
                    "hr": 139,
                    "agg_splats": 0,
                    "agg_calories": 7,
                    "timestamp": "2025-05-11T14:33:08Z",
                    "tread_data": {
                        "tread_speed": 2.24,
                        "tread_incline": 1.0,
                        "agg_tread_distance": 144
                    }
                },
                {
                    "relative_timestamp": 3243,
                    "hr": 128,
                    "agg_splats": 3,
                    "agg_calories": 410,
                    "timestamp": "2025-05-11T15:25:39Z"
                },
                {
                    "relative_timestamp": 3266,
                    "hr": 141,
                    "agg_splats": 3,
                    "agg_calories": 413,
                    "timestamp": "2025-05-11T15:26:02Z"
                },
                {
                    "relative_timestamp": 3289,
                    "hr": 143,
                    "agg_splats": 3,
                    "agg_calories": 416,
                    "timestamp": "2025-05-11T15:26:25Z"
                },
                {
                    "relative_timestamp": 3312,
                    "hr": 132,
                    "agg_splats": 3,
                    "agg_calories": 418,
                    "timestamp": "2025-05-11T15:26:48Z"
                },
                {
                    "relative_timestamp": 3335,
                    "hr": 135,
                    "agg_splats": 3,
                    "agg_calories": 421,
                    "timestamp": "2025-05-11T15:27:11Z"
                }
            ]
        }
    }
    """


if __name__ == "__main__":
    main()
