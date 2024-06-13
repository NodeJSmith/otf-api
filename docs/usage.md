# Usage

## Overview

To use the API, you need to create an instance of the `Api` class, providing your email address and password. This will authenticate you with the API and allow you to make requests. When the `Api` object is created it automatically grabs your member details and home studio, to simplify the process of making requests.

The `Api` object has multiple api objects as attributes, which you can use to make requests to the API. The available api objects are:

- `classes_api`
- `members_api`
- `performance_api`
- `studios_api`
- `telemetry_api`

Each of these api objects has methods that correspond to the endpoints in the API. You can use these methods to make requests to the API and get the data you need.

### Data

All of the endpoints return Pydantic models. The endpoints that return lists will generally be encapsulated in a list model, so that the top level data can still be dumped by Pydantic. For example, `get_workouts()` returns a `WorkoutList` which has a `workouts` attribute that contains the individual `Workout` items.

Below are some examples of how to use the API.

## Examples

### Get Upcoming Classes and Studio Details

```python

import asyncio
import json
import os

from otf_api import Api

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Api.create(USERNAME, PASSWORD)

    # To get upcoming classes you can call the `get_classes` method
    # You can pass a list of studio_uuids or, if you want to get classes from your home studio, leave it empty
    classes = await otf.classes_api.get_classes()
    print(json.dumps(classes.classes[0].model_dump(), indent=4, default=str))

    """
    {
        "id": "0e39ef70-7403-49c1-8605-4a72643bd201",
        "ot_base_class_uuid": "08cebfdb-e127-48d4-8a7f-e6ea4dd85c18",
        "starts_at": "2024-06-13 10:00:00+00:00",
        "starts_at_local": "2024-06-13 05:00:00",
        "ends_at": "2024-06-13 11:00:00+00:00",
        "ends_at_local": "2024-06-13 06:00:00",
        "name": "Orange 3G",
        "type": "ORANGE_60",
        "studio": ...,
        "coach": ...,
        "max_capacity": 36,
        "booking_capacity": 36,
        "waitlist_size": 0,
        "full": false,
        "waitlist_available": false,
        "canceled": false,
        "mbo_class_id": "30809",
        "mbo_class_schedule_id": "2655",
        "mbo_class_description_id": "102",
        "created_at": "2024-05-14 10:33:32.406000+00:00",
        "updated_at": "2024-06-13 01:58:55.233000+00:00"
    }
    """

    # if you need to figure out what studios are in an area, you can call `search_studios_by_geo`
    # which takes latitude, longitude, distance, page_index, and page_size as arguments
    # but you'll generally just need the first 3
    # same as with classes, you can leave it blank and get the studios within 50 miles of your home studio
    studios_by_geo = await otf.studios_api.search_studios_by_geo()
    print(json.dumps(studios_by_geo.studios[0].model_dump(), indent=4, default=str))

    """
    {
        "studio_id": 1297,
        "studio_uuid": "8645fb2b-ef66-4d9d-bda1-f508091ec891",
        "mbo_studio_id": 8612481,
        "studio_number": "05414",
        "studio_name": "AnyTown OH - East",
        "studio_physical_location_id": 494,
        "time_zone": "America/Chicago",
        "contact_email": "studiomanager05414@orangetheoryfitness.com",
        "studio_token": "ec2459b2-32b5-4b7e-9759-55270626925a",
        "environment": "PROD",
        "pricing_level": "",
        "tax_rate": "0.000000",
        "accepts_visa_master_card": true,
        "accepts_american_express": true,
        "accepts_discover": true,
        "accepts_ach": false,
        "is_integrated": true,
        "description": "",
        "studio_version": "",
        "studio_status": "Active",
        "open_date": "2017-01-13 00:00:00",
        "re_open_date": "2020-05-26 00:00:00",
        "studio_type_id": 2,
        "sms_package_enabled": false,
        "allows_dashboard_access": false,
        "allows_cr_waitlist": true,
        "cr_waitlist_flag_last_updated": "2020-07-09 02:43:55+00:00",
        "royalty_rate": 0,
        "marketing_fund_rate": 0,
        "commission_percent": 0,
        "is_mobile": null,
        "is_otbeat": null,
        "distance": 0.0,
        "studio_location": ...,
        "studio_location_localized": ...,
        "studio_profiles": {
            "is_web": true,
            "intro_capacity": 1,
            "is_crm": true
        },
        "social_media_links": ...
    }
    """

    # if you need to get detailed information about a studio, you can call `get_studio_detail`
    # which takes a studio_uuid as an argument, but you can leave it blank to get details about your home studio
    # this one has a result structure very much like the previous one
    studio_detail = await otf.studios_api.get_studio_detail()
    print(json.dumps(studio_detail.model_dump(), indent=4, default=str))


if __name__ == "__main__":
    asyncio.run(main())


```


### Challenge Tracker Data

```python
import asyncio
import json
import os

from otf_api import Api, ChallengeType, EquipmentType

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Api.create(USERNAME, PASSWORD)

    # challenge tracker content is an overview of the challenges OTF runs
    # and your participation in them
    challenge_tracker_content = await otf.member_api.get_challenge_tracker_content()
    print(json.dumps(challenge_tracker_content.benchmarks[0].model_dump(), indent=4, default=str))

    """
    {
        "equipment_id": 2,
        "equipment_name": "Treadmill",
        "years": [
            {
                "year": "2024",
                "is_participated": false,
                "in_progress": false
            },
            ...
        ],
        "logo_url": "https://otf-icons.s3.amazonaws.com/benchmarks/Treadmill.png"
    }
    """

    print(json.dumps(challenge_tracker_content.challenges[0].model_dump(), indent=4, default=str))
    """
    {
    "challenge_category_id": 10,
    "challenge_sub_category_id": 8,
    "challenge_name": "Catch Me If You Can 3G",
    "years": [
        {
            "year": "2024",
            "is_participated": false,
            "in_progress": false
        },
        ...
    ],
    "logo_url": "https://otf-icons.s3.amazonaws.com/challenges/CatchMeIfYouCan.png"
    }
    """

    # challenge tracker details are detailed information about specific challenges
    # this endpoint takes an equipment type and a challenge type as arguments
    tread_challenge_details = await otf.member_api.get_challenge_tracker_detail(
        EquipmentType.Treadmill, ChallengeType.Other
    )
    print(json.dumps(tread_challenge_details.details[0].model_dump(), indent=4, default=str))

    """
    {
        "challenge_category_id": 10,
        "challenge_sub_category_id": null,
        "equipment_id": 2,
        "equipment_name": "Treadmill",
        "metric_entry": {
            "title": "22 MIN",
            "equipment_id": 2,
            "entry_type": "Distance",
            "metric_key": "22MIN",
            "min_value": "0.16093440000000003",
            "max_value": "8.04672"
        },
        "challenge_name": "Catch me If You Can",
        "logo_url": "https://otf-icons.s3.amazonaws.com/challenges/CatchMeIfYouCan.png",
        "best_record": 1.40012928,
        "last_record": 1.40012928,
        "previous_record": 1.40012928,
        "unit": "km",
        "goals": null,
        "challenge_histories": [
            {
                "challenge_objective": "None",
                "challenge_id": 449906,
                "studio_id": 1267,
                "studio_name": "AnyTown OH - East",
                "start_date": "2024-02-06 00:00:00",
                "end_date": "2024-02-06 23:59:00",
                "total_result": 1.40012928,
                "is_finished": true,
                "benchmark_histories": [
                    {
                        "studio_name": "AnyTown OH - East",
                        "equipment_id": 2,
                        "result": 1.40012928,
                        "date_created": "2024-02-06 16:01:26",
                        "date_updated": "2024-02-06 16:01:26",
                        "class_time": "2024-02-06 09:45:00",
                        "challenge_sub_category_id": null,
                        "class_id": 86842386,
                        "substitute_id": 1,
                        "weight_lbs": 0,
                        "workout_type_id": null,
                        "workout_id": null,
                        "linked_challenges": []
                    }
                ]
            }
        ]
    }
    """


if __name__ == "__main__":
    asyncio.run(main())

```

### Get Workout Data

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
    telemetry = await otf.dna_api.get_telemetry(workouts.workouts[0].class_history_uuid)
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
