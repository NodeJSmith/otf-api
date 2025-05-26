from otf_api import Otf
from otf_api.models.workouts import ChallengeCategory, EquipmentType


def main():  # noqa: D103, ANN201
    otf = Otf()

    # You can get challenges by equipment or by challenge category

    for et in EquipmentType:
        benchmarks = otf.workouts.get_benchmarks_by_equipment(et)
        if not benchmarks:
            continue
        print(f"Equipment: {et.name}, Challenges: {len(benchmarks):,}")

        for b in benchmarks:
            print(f"{b.challenge_name} - {len(b.challenge_histories):,} entries")
            print(b.model_dump_json(indent=4))

            """
            {
                "challenge_category_id": 17,
                "challenge_sub_category_id": null,
                "equipment_id": 4,
                "equipment_name": "Rower",
                "metric_entry": {
                    "title": "2000 METER",
                    "equipment_id": 4,
                    "entry_type": "Time",
                    "metric_key": "2000METER",
                    "min_value": "05:00.00",
                    "max_value": "25:00.00"
                },
                "challenge_name": "2000 METER Row",
                "best_record": "10:49.48",
                "last_record": "10:49.48",
                "previous_record": "10:49.48",
                "unit": null,
                "goals": null,
                "challenge_histories": [
                    {
                        "studio_name": "AnyTown OH - East",
                        "start_date": "2025-01-16T00:00:00",
                        "end_date": "2025-01-16T23:59:00",
                        "total_result": "00:10:49.48",
                        "is_finished": true,
                        "benchmark_histories": [
                            {
                                "studio_name": "AnyTown OH - East",
                                "equipment_id": 4,
                                "class_time": "2025-01-16T09:45:00",
                                "challenge_sub_category_id": null,
                                "weight_lbs": 0,
                                "class_name": "Orange 60 Min 2G",
                                "coach_name": "Coach Coach",
                                "result": "10:49.48"
                            }
                        ]
                    }
                ]
            }

            """

    for ct in ChallengeCategory:
        benchmarks = otf.workouts.get_benchmarks_by_challenge_category(ct)
        if not benchmarks:
            continue
        print(f"Challenge Name: {ct.name}, Challenges: {len(benchmarks):,}")

        for b in benchmarks:
            print(f"{b.challenge_name} - {len(b.challenge_histories):,} entries")
            print(b.model_dump_json(indent=4))

            """
            {
                "challenge_category_id": 55,
                "challenge_sub_category_id": null,
                "equipment_id": 4,
                "equipment_name": "Rower",
                "metric_entry": {
                    "title": "23 MIN",
                    "equipment_id": 4,
                    "entry_type": "Distance",
                    "metric_key": "23MIN",
                    "min_value": "",
                    "max_value": ""
                },
                "challenge_name": "Inferno",
                "best_record": 2284.0,
                "last_record": 2284.0,
                "previous_record": 2284.0,
                "unit": "m",
                "goals": null,
                "challenge_histories": [
                    {
                        "studio_name": "AnyTown OH - East",
                        "start_date": "2024-05-14T00:00:00",
                        "end_date": "2024-05-14T23:59:00",
                        "total_result": 2284.0,
                        "is_finished": true,
                        "benchmark_histories": [
                            {
                                "studio_name": "AnyTown OH - East",
                                "equipment_id": 4,
                                "class_time": "2024-05-14T09:45:00",
                                "challenge_sub_category_id": null,
                                "weight_lbs": 0,
                                "class_name": "Orange 60 Min 2G",
                                "coach_name": "Coach Coach",
                                "result": 2284.0
                            }
                        ]
                    }
                ]
            }

            """


if __name__ == "__main__":
    main()
