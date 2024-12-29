import os

import pytest

from otf_api import Otf as Otf
from otf_api.models import ClassType, DoW


def test_get_classes_filters():
    username = os.getenv("OTF_EMAIL")
    password = os.getenv("OTF_PASSWORD")

    if not username or not password:
        raise ValueError("Please set OTF_EMAIL and OTF_PASSWORD environment variables")

    otf = Otf(username=username, password=password)

    with otf:
        classes = otf.get_classes(
            start_date="2024-12-29",
            end_date="2025-01-30",
            class_type=ClassType.ORANGE_3G,
            day_of_week=DoW.SATURDAY,
            include_home_studio=False,
        )

        assert len(classes)
