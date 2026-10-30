from datetime import date, datetime, time
from unittest.mock import patch

import pytest

from otf_api.models.bookings import ClassFilter, ClassType, DoW, OtfClass


def make_class(class_type: str) -> OtfClass:
    return OtfClass.model_validate(
        {
            "ot_base_class_uuid": "class-uuid",
            "name": "A class",
            "type": class_type,
            "ends_at_local": "2026-03-27T10:00:00",
            "starts_at_local": "2026-03-27T09:00:00",
            "studio": {"studioUUId": "studio-uuid"},
        }
    )


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
        ("HYROX_75", ["HYROX_75"]),
        ("hyrox 75", ["hyrox 75"]),
        ([ClassType.ORANGE_60, "HYROX_75"], [ClassType.ORANGE_60, "HYROX_75"]),
    ],
)
def test_class_type_unknown_value_is_accepted(provided, expected):
    assert ClassFilter(class_type=provided).class_type == expected


@pytest.mark.parametrize("provided", ["HYROX_75", "hyrox 75", " Hyrox_75 ", ["hyrox 75", "ORANGE_60"]])
def test_filter_matches_unknown_class_type_ignoring_case_and_spaces(provided):
    hyrox = make_class("HYROX_75")
    tread = make_class("TREAD_50")

    assert ClassFilter(class_type=provided).filter_classes([hyrox, tread]) == [hyrox]


def test_filter_known_type_matches_only_that_type():
    orange = make_class("ORANGE_60")
    hyrox = make_class("HYROX_75")

    assert ClassFilter(class_type="orange 60").filter_classes([orange, hyrox]) == [orange]


def test_filter_typo_matches_nothing_instead_of_raising():
    assert ClassFilter(class_type="orang 60").filter_classes([make_class("ORANGE_60")]) == []


def test_filter_warns_on_each_construction_with_an_unknown_value():
    with patch("otf_api.models.bookings.filters.LOGGER.warning") as warning:
        ClassFilter(class_type="orang 60")
        ClassFilter(class_type="orang 60")
        ClassFilter(class_type="ORANGE 60")

    assert warning.call_count == 2


def test_filter_class_type_set_after_construction_still_matches():
    orange = make_class("ORANGE_60")
    cf = ClassFilter()
    cf.class_type = ClassType.ORANGE_60

    assert cf.filter_classes([orange, make_class("TREAD_50")]) == [orange]


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
