from datetime import datetime
from enum import Enum
from typing import ClassVar

from humanize import precisedelta
from inflection import humanize
from pydantic import Field
from rich.style import Style
from rich.styled import Styled
from rich.table import Table

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
    def get_case_insensitive(cls, value: str) -> str:
        lcase_to_actual = {item.value.lower(): item.value for item in cls}
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
    def all_statuses(cls) -> list[str]:
        return list(cls.__members__.values())

    @classmethod
    def get_from_key_insensitive(cls, key: str) -> "ClassType":
        lcase_to_actual = {item.lower(): item for item in cls._member_map_}
        val = cls.__members__.get(lcase_to_actual[key.lower()])
        if not val:
            raise ValueError(f"Invalid ClassType: {key}")
        return val

    @classmethod
    def get_case_insensitive(cls, value: str) -> str:
        lcase_to_actual = {item.value.lower(): item.value for item in cls}
        return lcase_to_actual[value.lower()]


class ClassTypeCli(str, Enum):
    """Flipped enum so that the CLI does not have values with spaces"""

    ORANGE_60_MIN_2G = "Orange_60_Min_2G"
    TREAD_50 = "Tread_50"
    STRENGTH_50 = "Strength_50"
    ORANGE_3G = "Orange_3G"
    ORANGE_60_TORNADO = "Orange_60_Tornado"
    ORANGE_TORNADO = "Orange_Tornado"
    ORANGE_90_MIN_3G = "Orange_90_Min_3G"
    VIP_CLASS = "VIP_Class"
    OTHER = "Other"


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
    def id_val(self) -> str:
        return self.ot_class_uuid

    @property
    def day_of_week_enum(self) -> DoW:
        dow = self.starts_at_local.strftime("%A")
        return DoW.get_case_insensitive(dow)

    @property
    def sidebar_data(self) -> Table:
        data = {
            "class_date": self.date,
            "class_time": self.time.strip(),
            "class_name": self.name,
            "class_id": self.id_val,
            "available": self.has_availability,
            "waitlist_available": self.waitlist_available,
            "studio_address": self.studio.address.line1,
            "coach_name": self.coach.first_name,
            "waitlist_size": self.waitlist_size,
            "max_capacity": self.max_capacity,
        }

        if not self.full:
            del data["waitlist_available"]
            del data["waitlist_size"]

        table = Table(expand=True, show_header=False, show_footer=False)
        table.add_column("Key", style="cyan", ratio=1)
        table.add_column("Value", style="magenta", ratio=2)

        for key, value in data.items():
            if value is False:
                table.add_row(key, Styled(str(value), style="red"))
            else:
                table.add_row(key, str(value))

        return table

    def get_style(self, is_selected: bool = False) -> Style:
        style = super().get_style(is_selected)
        if self.is_booked:
            style = Style(color="grey58")
        return style

    @classmethod
    def attr_to_column_header(cls, attr: str) -> str:
        attr_map = {k: humanize(k) for k in cls.model_fields}
        overrides = {
            "day_of_week": "Class DoW",
            "date": "Class Date",
            "time": "Class Time",
            "duration": "Class Duration",
            "name": "Class Name",
            "is_home_studio": "Home Studio",
            "is_booked": "Booked",
        }

        attr_map.update(overrides)

        return attr_map.get(attr, attr)


class OtfClassList(OtfListBase):
    collection_field: ClassVar[str] = "classes"
    classes: list[OtfClass]

    @staticmethod
    def book_class_columns() -> list[str]:
        return [
            "day_of_week",
            "date",
            "time",
            "duration",
            "name",
            "studio.name",
            "is_home_studio",
            "is_booked",
        ]

    def to_table(self, columns: list[str] | None = None) -> Table:
        if not columns:
            columns = self.book_class_columns()

        return super().to_table(columns)
