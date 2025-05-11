from contextlib import suppress

from otf_api import Otf
from otf_api.exceptions import AlreadyRatedError, ClassNotRatableError
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

    # you can get a list of workouts by calling `get_workouts`, which optionally takes a start and end date
    # the workout includes all of the details, including the performance summary, class, coach, studio, and rating data
    # from the new endpoint
    data_list = otf.get_workouts()
    print(data_list[0].model_dump_json(indent=4))
    # TODO: update the example data to match the new model
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
    # the method returns an updated PerformanceSummary object

    # if you already rated the class it will return an exception
    # likewise if the class is not ratable (seems to be an age cutoff) or if the class is not found
    with suppress(AlreadyRatedError, ClassNotRatableError):
        res = otf.rate_class_from_workout(data_list[0], 3, 3)
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


if __name__ == "__main__":
    main()
