# com/orangetheoryfitness/fragment/rating/RateStatus.java

# we convert these to the new values that the app uses
# mainly because we don't want to cause any issues with the API and/or with OTF corporate
# wondering where the old values are coming from

COACH_RATING_MAP = {0: 0, 1: 16, 2: 17, 3: 18}
CLASS_RATING_MAP = {0: 0, 1: 19, 2: 20, 3: 21}


def get_class_rating_value(class_rating: int) -> int:
    """Convert the class rating from the old values to the new values."""
    if class_rating not in CLASS_RATING_MAP:
        raise ValueError(f"Invalid class rating {class_rating}")

    return CLASS_RATING_MAP[class_rating]


def get_coach_rating_value(coach_rating: int) -> int:
    """Convert the coach rating from the old values to the new values."""
    if coach_rating not in COACH_RATING_MAP:
        raise ValueError(f"Invalid coach rating {coach_rating}")

    return COACH_RATING_MAP[coach_rating]
