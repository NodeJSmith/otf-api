import asyncio
import os

from otf_api import Otf
from otf_api.models.responses import ChallengeType, EquipmentType

USERNAME = os.getenv("OTF_EMAIL")
PASSWORD = os.getenv("OTF_PASSWORD")


async def main():
    otf = await Otf.create(USERNAME, PASSWORD)

    # challenge tracker content is an overview of the challenges OTF runs
    # and your participation in them
    challenge_tracker_content = await otf.get_challenge_tracker_content()
    print(challenge_tracker_content.benchmarks[0].model_dump_json(indent=4))

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

    print(challenge_tracker_content.challenges[0].model_dump_json(indent=4))
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
    tread_challenge_details = await otf.get_challenge_tracker_detail(EquipmentType.Treadmill, ChallengeType.Other)
    print(tread_challenge_details.details[0].model_dump_json(indent=4))

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
