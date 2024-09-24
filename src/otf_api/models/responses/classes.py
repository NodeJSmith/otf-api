from datetime import datetime
from enum import Enum
from typing import ClassVar

from humanize import precisedelta
from pydantic import Field

from otf_api.models.base import OtfItemBase, OtfListBase


class DoW(str, Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

    @classmethod
    def get_case_insensitive(cls, value: str) -> "DoW":
        lcase_to_actual = {item.value.lower(): item for item in cls}
        return lcase_to_actual[value.lower()]


class ClassType(str, Enum):
    ORANGE_60_MIN_2G = "Orange 60 Min 2G"
    TREAD_50 = "Tread 50"
    STRENGTH_50 = "Strength 50"
    ORANGE_3G = "Orange 3G"
    ORANGE_60_TORNADO = "Orange 60 - Tornado"
    ORANGE_TORNADO = "Orange Tornado"
    ORANGE_90_MIN_3G = "Orange 90 Min 3G"
    VIP_CLASS = "VIP Class"
    OTHER = "Other"

    @classmethod
    def get_case_insensitive(cls, value: str) -> str:
        lcase_to_actual = {item.value.lower(): item.value for item in cls}
        return lcase_to_actual[value.lower()]


class Address(OtfItemBase):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str


class Studio(OtfItemBase):
    id: str
    name: str
    mbo_studio_id: str
    time_zone: str
    currency_code: str
    address: Address
    phone_number: str
    latitude: float
    longitude: float


class Coach(OtfItemBase):
    mbo_staff_id: str
    first_name: str
    image_url: str | None = None


class OtfClassTimeMixin:
    starts_at_local: datetime
    ends_at_local: datetime
    name: str

    @property
    def day_of_week(self) -> str:
        return self.starts_at_local.strftime("%A")

    @property
    def date(self) -> str:
        return self.starts_at_local.strftime("%Y-%m-%d")

    @property
    def time(self) -> str:
        """Returns time in 12 hour clock format, with no leading 0"""
        val = self.starts_at_local.strftime("%I:%M %p")
        if val[0] == "0":
            val = " " + val[1:]

        return val

    @property
    def duration(self) -> str:
        duration = self.ends_at_local - self.starts_at_local
        human_val: str = precisedelta(duration, minimum_unit="minutes")
        if human_val == "1 hour and 30 minutes":
            return "90 minutes"
        return human_val

    @property
    def class_type(self) -> ClassType:
        for class_type in ClassType:
            if class_type.value in self.name:
                return class_type

        return ClassType.OTHER


class OtfClass(OtfItemBase, OtfClassTimeMixin):
    id: str
    ot_class_uuid: str = Field(
        alias="ot_base_class_uuid",
        description="The OTF class UUID, this is what shows in a booking response and how you can book a class.",
    )
    starts_at: datetime
    starts_at_local: datetime
    ends_at: datetime
    ends_at_local: datetime
    name: str
    type: str
    studio: Studio
    coach: Coach
    max_capacity: int
    booking_capacity: int
    waitlist_size: int
    full: bool
    waitlist_available: bool
    canceled: bool
    mbo_class_id: str
    mbo_class_schedule_id: str
    mbo_class_description_id: str
    created_at: datetime
    updated_at: datetime
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")
    is_booked: bool | None = Field(None, description="Custom helper field to determine if class is already booked")

    @property
    def has_availability(self) -> bool:
        return not self.full

    @property
    def day_of_week_enum(self) -> DoW:
        dow = self.starts_at_local.strftime("%A")
        return DoW.get_case_insensitive(dow)


class OtfClassList(OtfListBase):
    collection_field: ClassVar[str] = "classes"
    classes: list[OtfClass]
