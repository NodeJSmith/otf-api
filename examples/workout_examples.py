import os
from getpass import getpass

from otf_api import Otf, OtfUser

USERNAME = os.getenv("OTF_EMAIL") or input("Enter your OTF email: ")
PASSWORD = os.getenv("OTF_PASSWORD") or getpass("Enter your OTF password: ")


def main():
    otf = Otf(user=OtfUser(USERNAME, PASSWORD))

    resp = otf.get_member_lifetime_stats()
    print(resp.model_dump_json(indent=4))

    resp = otf.get_body_composition_list()
    print(resp.data[0].model_dump_json(indent=4))

    # performance summaries are historical records of your performance in workouts
    # `get_performance_summaries` takes a limit (default of 30) and returns a list of summaries
    data_list = otf.get_performance_summaries()
    print(data_list.summaries[0].model_dump_json(indent=4))
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
        "otf_class": {
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
    data = otf.get_performance_summary(data_list.summaries[0].id)
    print(data.model_dump_json(indent=4))

    """
    {
        "class_history_uuid": "29dd97f4-3418-4247-b35c-37eabc5e17f3",
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
        "otf_class": {
            "starts_at_local": "2024-06-11T09:45:00",
            "name": "Orange 60 Min 2G"
        }
    }
    """

    # telemetry is a detailed record of a specific workout - minute by minute, or more granular if desired
    # this endpoint takes a class_history_uuid, as well as a number of max data points - if you do not pass
    # this value it will attempt to return enough data points for 30 second intervals

    telemetry = otf.get_telemetry(performance_summary_id=data_list.summaries[0].id)
    telemetry.telemetry = telemetry.telemetry[:2]
    print(telemetry.model_dump_json(indent=4))

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
                },
                "row_data": {
                    "row_speed": 1.0,
                    "row_pps": 0.0,
                    "row_Spm": 0.0,
                    "agg_row_distance": 0,
                    "row_pace": 0
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
                },
                "row_data": {
                    "row_speed": 1.0,
                    "row_pps": 0.0,
                    "row_Spm": 0.0,
                    "agg_row_distance": 0,
                    "row_pace": 0
                }
            },
            ...
        ]
    }
    """


if __name__ == "__main__":
    main()
