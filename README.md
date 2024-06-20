Simple API client for interacting with the OrangeTheory Fitness APIs.


This library allows access to the OrangeTheory API to retrieve workouts and performance data, class schedules, studio information, and bookings. It is a work in progress, currently only allowing access to GET calls, but my goal is to expand it to include POST, PUT, and DELETE calls as well.

## Installation
```bash
pip install otf-api
```

## Overview

To use the API, you need to create an instance of the `Api` class, providing your email address and password. This will authenticate you with the API and allow you to make requests. When the `Api` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

The `Api` object has multiple api objects as attributes, which you can use to make requests to the API. The available api objects are:

- `classes_api`
- `members_api`
- `performance_api`
- `studios_api`
- `telemetry_api`


## Example Usage

Note: see more examples in the `examples` directory and in the [usage docs](https://otf-api.readthedocs.io/en/stable/usage/).

```python
import asyncio
import json
import os

from otf_api import Api

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Api.create(USERNAME, PASSWORD)

    # performance summaries are historical records of your performance in workouts
    # `get_performance_summaries` takes a limit (default of 30) and returns a list of summaries
    data_list = await otf.performance_api.get_performance_summaries()
    print(json.dumps(data_list.summaries[0].model_dump(), indent=4, default=str))
    """
    {
        "performance_summary_id": "29dd97f4-3418-4247-b35c-37eabc5e17f3",
        "details": {
            "calories_burned": 506,
            "splat_points": 18,
            "step_count": 0,
            "active_time_seconds": 3413,
            "zone_time_minutes": {
                "gray": 2,
                "blue": 13,
                "green": 24,
                "orange": 16,
                "red": 2
            }
        },
        "ratable": true,
        "class_": {
            "ot_base_class_uuid": "b6549fc2-a479-4b03-9303-e0e45dbcd8c9",
            "starts_at_local": "2024-06-11T09:45:00",
            "name": "Orange 60 Min 2G",
            "coach": ...,
            "studio": ...,
        },
        "ratings": null
    }
    """

    # you can get detailed information about a specific performance summary by calling `get_performance_summary`
    # which takes a performance_summary_id as an argument
    data = await otf.performance_api.get_performance_summary(data_list.summaries[0].performance_summary_id)
    print(json.dumps(data.model_dump(), indent=4, default=str))

    """
    {
        "id": "29dd97f4-3418-4247-b35c-37eabc5e17f3",
        "details": {
            "calories_burned": 506,
            "splat_points": 18,
            "step_count": 3314,
            "active_time_seconds": 0,
            "zone_time_minutes": {
                "gray": 2,
                "blue": 13,
                "green": 24,
                "orange": 16,
                "red": 2
            },
            "heart_rate": {
                "max_hr": 0,
                "peak_hr": 180,
                "peak_hr_percent": 94,
                "avg_hr": 149,
                "avg_hr_percent": 78
            },
            "equipment_data": {
                "treadmill": {
                    "avg_pace": {
                        "display_value": "15:23",
                        "display_unit": "min/mile",
                        "metric_value": "923"
                    },
                    "avg_speed": {
                        "display_value": 3.9,
                        "display_unit": "mph",
                        "metric_value": 3.9
                    },
                    "max_pace": ...,
                    "max_speed": ...,
                    "moving_time": ...,
                    "total_distance": ...,
                    "avg_incline": ...,
                    "elevation_gained": ...,
                    "max_incline": ...
                },
                "rower": ...
            }
        },
        "ratable": false,
        "class_": {
            "starts_at_local": "2024-06-11T09:45:00",
            "name": "Orange 60 Min 2G"
        }
    }
    """

    # workouts is a similar endpoint but returns more data - this is what OTLive uses to display workout history
    # this endpoint takes no arguments and returns all workouts back to, as far as we can tell, around 2019
    workouts = await otf.member_api.get_workouts()
    print(json.dumps(workouts.workouts[0].model_dump(), indent=4, default=str))
    """
    {
        "studio_number": "8292",
        "studio_name": "AnyTown OH - East",
        "class_type": "Orange 60 Min 2G",
        "active_time": 3413,
        "coach": "Coach",
        "member_uuid": "b4df31a6-fa54-4a7f-85eb-1f5b613c6414",
        "class_date": "2024-06-11 09:45:00+00:00",
        "total_calories": 506,
        "avg_hr": 149,
        "max_hr": 180,
        "avg_percent_hr": 78,
        "max_percent_hr": 94,
        "total_splat_points": 18,
        "red_zone_time_second": 137,
        "orange_zone_time_second": 979,
        "green_zone_time_second": 1415,
        "blue_zone_time_second": 769,
        "black_zone_time_second": 113,
        "step_count": 3314,
        "class_history_uuid": "c71658c3-46e7-410b-8ffa-9a8ffd3828fa",
        "class_id": "30299",
        "date_created": "2024-06-11 10:43:00+00:00",
        "date_updated": "2024-06-11 10:43:00+00:00",
        "is_intro": false,
        "is_leader": false,
        "member_email": null,
        "member_name": "Member Name",
        "member_performance_id": "0cbc39d3-bb9b-4021-8006-8eb23c272f0d",
        "minute_by_minute_hr": [
            108,
            147,
            149,
           ...
        ],
        "source": "OTbeat Live",
        "studio_account_uuid": "studio-number-0325",
        "version": "1",
        "workout_type": {
            "id": 101,
            "display_name": "Studio Workout",
            "icon": ""
        }
    }
    """

    # telemetry is a detailed record of a specific workout - minute by minute, or more granular if desired
    # this endpoint takes a class_history_uuid, as well as a number of max data points - if you do not pass
    # this value it will attempt to return enough data points for 30 second intervals
    telemetry = await otf.telemetry_api.get_telemetry(workouts.workouts[0].class_history_uuid)
    print(json.dumps(telemetry.model_dump(), indent=4, default=str))

    """
    {
        "member_uuid": "fa323d40-bfae-4e72-872c-e11188d182a7",
        "class_history_uuid": "5945a723-930b-449a-bd8f-8267a4ff392f",
        "class_start_time": "2024-06-11 14:46:07+00:00",
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
        "window_size": 30,
        "telemetry": [
            {
                "relative_timestamp": 0,
                "hr": 105,
                "agg_splats": 0,
                "agg_calories": 2,
                "timestamp": "2024-06-11 14:46:07+00:00",
                "tread_data": {
                    "tread_speed": 1.34,
                    "tread_incline": 1.0,
                    "agg_tread_distance": 9
                }
            },
            {
                "relative_timestamp": 30,
                "hr": 132,
                "agg_splats": 0,
                "agg_calories": 4,
                "timestamp": "2024-06-11 14:46:37+00:00",
                "tread_data": {
                    "tread_speed": 2.46,
                    "tread_incline": 1.0,
                    "agg_tread_distance": 62
                }
            },
            ...
        ]
    }
    """


if __name__ == "__main__":
    asyncio.run(main())

```


Disclaimer:
This project is in no way affiliated with OrangeTheory Fitness.
