from otf_api import Otf
from otf_api.models import ChallengeType, EquipmentType


def main():
    otf = Otf()

    # challenge tracker content is an overview of the challenges OTF runs
    # and your participation in them
    challenge_tracker_content = otf.get_challenge_tracker()
    print(challenge_tracker_content.benchmarks[0].model_dump_json(indent=4))

    """
    {
        "equipment_id": 2,
        "equipment_name": "Treadmill",
        "years": [
            {
                "year": 2025,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2024,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2023,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2022,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2021,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2020,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2019,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2018,
                "is_participated": false,
                "in_progress": false
            }
        ]
    }

    """

    print(challenge_tracker_content.challenges[0].model_dump_json(indent=4))

    """
    {
        "challenge_name": "Catch Me If You Can 3G",
        "years": [
            {
                "year": 2025,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2024,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2023,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2022,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2021,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2020,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2019,
                "is_participated": false,
                "in_progress": false
            },
            {
                "year": 2018,
                "is_participated": false,
                "in_progress": false
            }
        ]
    }

    """

    # challenge tracker details are detailed information about specific challenges
    # this endpoint takes an equipment type and a challenge type as arguments
    tread_challenge_details = otf.get_benchmarks(EquipmentType.Treadmill, ChallengeType.Other)
    print(tread_challenge_details[0].model_dump_json(indent=4))

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
        "best_record": 1.40012928,
        "last_record": 1.3679424,
        "previous_record": 1.40012928,
        "unit": "km",
        "goals": null,
        "challenge_histories": [
            {
                "studio_name": "AnyTown OH - East",
                "start_date": "2024-08-22T00:00:00",
                "end_date": "2024-08-22T23:59:00",
                "total_result": 1.3679424,
                "is_finished": true,
                "benchmark_histories": [
                    {
                        "studio_name": "AnyTown OH - East",
                        "equipment_id": 2,
                        "class_time": "2024-08-22T09:45:00",
                        "challenge_sub_category_id": null,
                        "weight_lbs": 0,
                        "class_name": "Orange 60 Min 2G",
                        "coach_name": "Coach Coach",
                        "result": 1.3679424,
                        "workout_type_id": null,
                        "workout_id": null
                    }
                ]
            },
            {
                "studio_name": "AnyTown OH - East",
                "start_date": "2024-02-06T00:00:00",
                "end_date": "2024-02-06T23:59:00",
                "total_result": 1.40012928,
                "is_finished": true,
                "benchmark_histories": [
                    {
                        "studio_name": "AnyTown OH - East",
                        "equipment_id": 2,
                        "class_time": "2024-02-06T09:45:00",
                        "challenge_sub_category_id": null,
                        "weight_lbs": 0,
                        "class_name": "Orange 60 Min 2G",
                        "coach_name": "Coach Coach",
                        "result": 1.40012928,
                        "workout_type_id": null,
                        "workout_id": null
                    }
                ]
            }
        ]
    }
    """


if __name__ == "__main__":
    main()
