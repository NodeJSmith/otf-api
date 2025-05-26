from contextlib import suppress

from otf_api import Otf
from otf_api.exceptions import AlreadyRatedError, ClassNotRatableError
from otf_api.models.workouts import StatsTime


def main():  # noqa: D103, ANN201
    otf = Otf()

    resp = otf.workouts.get_member_lifetime_stats_in_studio()
    print("Lifetime in-studio stats:")
    print(resp.model_dump_json(indent=4))

    """
    {
        "calories": 53064.0,
        "splat_point": 1611.0,
        "total_black_zone": 28585.0,
        "total_blue_zone": 81156.0,
        "total_green_zone": 170131.0,
        "total_orange_zone": 80405.0,
        "total_red_zone": 16739.0,
        "workout_duration": 0.0,
        "step_count": 466842.0,
        "treadmill_distance": 328965.0,
        "treadmill_elevation_gained": 5107.705701113568,
        "rower_distance": 52206.0,
        "rower_watt": 12102.222261852763
    }
    """

    resp = otf.workouts.get_member_lifetime_stats_in_studio(StatsTime.ThisMonth)
    print("This month in-studio stats:")
    print(resp.model_dump_json(indent=4))

    """
    {
        "calories": 2703.0,
        "splat_point": 42.0,
        "total_black_zone": 3455.0,
        "total_blue_zone": 6572.0,
        "total_green_zone": 9079.0,
        "total_orange_zone": 2517.0,
        "total_red_zone": 9.0,
        "workout_duration": 0.0,
        "step_count": 22249.0,
        "treadmill_distance": 15800.0,
        "treadmill_elevation_gained": 201.71490890395847,
        "rower_distance": 4110.0,
        "rower_watt": 931.8466484189851
    }
    """

    # you can get a list of workouts by calling `get_workouts`, which optionally takes a start and end date
    # the workout includes all of the details, including the performance summary, class, coach, studio, and rating data
    # from the new endpoint - the data matches what is shown in the OTF app after a workout
    data_list = otf.workouts.get_workouts()
    print(data_list[0].model_dump_json(indent=4, exclude_none=True))
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

    # if you want to rate a class you can do that with the `rate_class_from_workout` method
    # this method takes a workout object, as well as a coach_rating and class_rating
    # the ratings are integers from 1 - 3
    # the method returns an updated Workout object

    # if you already rated the class it will return an exception
    # likewise if the class is not ratable (seems to be an age cutoff) or if the class is not found
    with suppress(AlreadyRatedError, ClassNotRatableError):
        unrated_class = next((w for w in data_list if w.ratable and not w.class_rating), None)
        if unrated_class:
            rated_workout = otf.workouts.rate_class_from_workout(unrated_class, 3, 3)
            print(rated_workout.model_dump_json(indent=4))
        else:
            print("No unrated classes found")


if __name__ == "__main__":
    main()
