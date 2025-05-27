from datetime import date, datetime, time

import pytest

from otf_api.models.bookings import ClassFilter, ClassType, DoW


def test_class_filter_string_to_date():
    cf = ClassFilter(start_date="2024-12-29", end_date="2025-01-30")
    assert cf.start_date == date(2024, 12, 29)
    assert cf.end_date == date(2025, 1, 30)


def test_class_filter_datetime_str_to_date():
    cf = ClassFilter(start_date="2024-12-29T00:00:00", end_date="2025-01-30T00:00:00")
    assert cf.start_date == date(2024, 12, 29)
    assert cf.end_date == date(2025, 1, 30)


def test_class_filter_datetime_object_to_date():
    cf = ClassFilter(start_date=datetime(2024, 12, 29), end_date=datetime(2025, 1, 30))
    assert cf.start_date == date(2024, 12, 29)
    assert cf.end_date == date(2025, 1, 30)


def test_class_filter_single_item_to_list():
    cf = ClassFilter(class_type=ClassType.ORANGE_90)
    assert cf.class_type == [ClassType.ORANGE_90]

    cf = ClassFilter(start_time=time(12, 30))
    assert cf.start_time == [time(12, 30)]

    cf = ClassFilter(day_of_week=DoW.SUNDAY)
    assert cf.day_of_week == [DoW.SUNDAY]


@pytest.mark.parametrize(
    ["provided", "expected"],
    [
        ("ORANGE 60", [ClassType.ORANGE_60]),
        ("orange 60 ", [ClassType.ORANGE_60]),
        ([ClassType.ORANGE_60, "ORANGE 60"], [ClassType.ORANGE_60, ClassType.ORANGE_60]),
    ],
)
def test_class_type_str_to_enum(provided, expected):
    cf = ClassFilter(class_type=provided)
    assert cf.class_type == expected


@pytest.mark.parametrize(
    ["provided", "expected"],
    [
        ("Sunday", [DoW.SUNDAY]),
        ("sunday", [DoW.SUNDAY]),
        (["Sunday"], [DoW.SUNDAY]),
        ([DoW.SUNDAY, "Monday"], [DoW.SUNDAY, DoW.MONDAY]),
    ],
)
def test_day_of_week_str_to_enum(provided, expected):
    cf = ClassFilter(day_of_week=provided)
    assert cf.day_of_week == expected


@pytest.mark.parametrize(
    ["provided", "expected"],
    [
        ("12:30", [time(12, 30)]),
        ("12:30", [time(12, 30)]),
        (["12:30"], [time(12, 30)]),
        ([time(12, 30), "13:45"], [time(12, 30), time(13, 45)]),
    ],
)
def test_class_filter_string_time(provided, expected):
    cf = ClassFilter(start_time=provided)
    assert cf.start_time == expected
