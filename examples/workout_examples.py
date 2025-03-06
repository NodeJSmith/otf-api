from contextlib import suppress

from otf_api import Otf
from otf_api.exceptions import AlreadyRatedError
from otf_api.models.enums import StatsTime


def main():
    otf = Otf()

    resp = otf.get_member_lifetime_stats_in_studio()
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

    resp = otf.get_member_lifetime_stats_in_studio(StatsTime.ThisMonth)
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

    # performance summaries are historical records of your performance in workouts
    # `get_performance_summaries` takes a limit (default of 5) and returns a list of summaries
    data_list = otf.get_performance_summaries(200)
    print(data_list[0].model_dump_json(indent=4))
    """
    {
        "id": "c39e7cde-5e02-4e1a-89e2-d41e8a4653b3",
        "calories_burned": 250,
        "splat_points": 0,
        "step_count": 0,
        "active_time_seconds": 2687,
        "zone_time_minutes": {
            "gray": 17,
            "blue": 24,
            "green": 4,
            "orange": 0,
            "red": 0
        },
        "ratable": true,
        "otf_class": {
            "class_uuid": "23c8ad3e-4257-431c-b5f0-8313d8d82434",
            "starts_at": "2025-01-18T10:30:00",
            "name": "Tread 50 / Strength 50",
            "type": "STRENGTH_50"
        },
        "coach": "Bobby",
        "coach_rating": null,
        "class_rating": null
    }
    """

    # if you want to rate a class you can do that with the `rate_class_from_performance_summary` method
    # this method takes a performance_summary object, as well as a coach_rating and class_rating
    # the ratings are integers from 1 - 3
    # the method returns an updated PerformanceSummaryEntry object

    # if you already rated the class it will return an exception
    # likewise if the class is not ratable (seems to be an age cutoff) or if the class is not found
    with suppress(AlreadyRatedError):
        res = otf.rate_class_from_performance_summary(data_list[0], 3, 3)
        print(res.model_dump_json(indent=4))

    """
    {
        "id": "c39e7cde-5e02-4e1a-89e2-d41e8a4653b3",
        "calories_burned": 250,
        "splat_points": 0,
        "step_count": 0,
        "active_time_seconds": 2687,
        "zone_time_minutes": {
            "gray": 17,
            "blue": 24,
            "green": 4,
            "orange": 0,
            "red": 0
        },
        "ratable": true,
        "otf_class": {
            "class_uuid": "23c8ad3e-4257-431c-b5f0-8313d8d82434",
            "starts_at": "2025-01-18T10:30:00",
            "name": "Tread 50 / Strength 50",
            "type": "STRENGTH_50"
        },
        "coach": "Bobby",
        "coach_rating": {
            "id": "18",
            "description": "Double Thumbs Up",
            "value": 3
        },
        "class_rating": {
            "id": "21",
            "description": "Double Thumbs Up",
            "value": 3
        }
    }
    """

    # you can get detailed information about a specific performance summary by calling `get_performance_summary`
    # which takes a performance_summary_id as an argument
    data = otf.get_performance_summary(data_list[0].class_history_uuid)
    print(data.model_dump_json(indent=4))

    """
    {
        "id": "8cd3a800-3ac1-4142-8b75-0c00bc19866c",
        "class_name": "Orange 60 Min 2G",
        "class_starts_at": "2025-01-16T09:45:00",
        "ratable": false,
        "calories_burned": 448,
        "splat_points": 11,
        "step_count": 3008,
        "active_time_seconds": 0,
        "zone_time_minutes": {
            "gray": 7,
            "blue": 9,
            "green": 28,
            "orange": 11,
            "red": 0
        },
        "heart_rate": {
            "max_hr": 0,
            "peak_hr": 176,
            "peak_hr_percent": 92,
            "avg_hr": 142,
            "avg_hr_percent": 74
        },
        "rower_data": {
            "avg_pace": {
                "display_value": "00:02:31",
                "display_unit": "min/500m",
                "metric_value": 151.0
            },
            "avg_speed": {
                "display_value": 13.3,
                "display_unit": "km/h",
                "metric_value": 13.3
            },
            "max_pace": {
                "display_value": "00:01:43",
                "display_unit": "min/500m",
                "metric_value": 103.0
            },
            "max_speed": {
                "display_value": 17.4,
                "display_unit": "km/h",
                "metric_value": 17.4
            },
            "moving_time": {
                "display_value": "00:10:49",
                "display_unit": "Duration",
                "metric_value": 649.0
            },
            "total_distance": {
                "display_value": 2000.0,
                "display_unit": "m",
                "metric_value": 2000.0
            },
            "avg_cadence": {
                "display_value": 19.5,
                "display_unit": "",
                "metric_value": 19.5
            },
            "avg_power": {
                "display_value": 125.0,
                "display_unit": "watt",
                "metric_value": 125.0
            },
            "max_cadence": {
                "display_value": 39.0,
                "display_unit": "",
                "metric_value": 39.0
            }
        },
        "treadmill_data": {
            "avg_pace": {
                "display_value": "00:16:13",
                "display_unit": "min/mile",
                "metric_value": 973.0
            },
            "avg_speed": {
                "display_value": 3.7,
                "display_unit": "mph",
                "metric_value": 3.7
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
                "display_value": "00:18:41",
                "display_unit": "Duration",
                "metric_value": 1121.0
            },
            "total_distance": {
                "display_value": 1.34,
                "display_unit": "miles",
                "metric_value": 1.34
            },
            "avg_incline": {
                "display_value": 1.6,
                "display_unit": "%",
                "metric_value": 1.6
            },
            "elevation_gained": {
                "display_value": 113.843,
                "display_unit": "feet",
                "metric_value": 113.843
            },
            "max_incline": {
                "display_value": 10.0,
                "display_unit": "%",
                "metric_value": 10.0
            }
        }
    }
    """

    # telemetry is a detailed record of a specific workout - minute by minute, or more granular if desired
    # this endpoint takes a class_history_uuid, as well as a number of max data points (default 120)

    telemetry = otf.get_telemetry(performance_summary_id=data_list[1].class_history_uuid)
    telemetry.telemetry = telemetry.telemetry[:2]
    print(telemetry.model_dump_json(indent=4))

    """
    {
        "member_uuid": "7d2f2b96-7e03-426e-b1dd-39491b79222f",
        "class_history_uuid": "fcff805a-4e0c-4606-9976-5e85a54dc972",
        "class_start_time": "2025-01-16T15:47:25Z",
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
        "window_size": 28,
        "telemetry": [
            {
                "relative_timestamp": 0,
                "hr": 97,
                "agg_splats": 0,
                "agg_calories": 1,
                "timestamp": "2025-01-16T15:47:25Z",
                "tread_data": {
                    "tread_speed": 2.24,
                    "tread_incline": 1.0,
                    "agg_tread_distance": 24
                },
                "row_data": null
            },
            {
                "relative_timestamp": 28,
                "hr": 127,
                "agg_splats": 0,
                "agg_calories": 4,
                "timestamp": "2025-01-16T15:47:53Z",
                "tread_data": {
                    "tread_speed": 2.46,
                    "tread_incline": 1.0,
                    "agg_tread_distance": 78
                },
                "row_data": null
            }
        ]
    }

    """


if __name__ == "__main__":
    main()
