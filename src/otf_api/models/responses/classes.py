from datetime import datetime
from enum import Enum

from humanize import precisedelta
from pydantic import Field
from rich.style import Style
from rich.styled import Styled
from rich.table import Table

from otf_api.models.base import OtfBaseModel


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


class Address(OtfBaseModel):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str


class Studio(OtfBaseModel):
    id: str
    name: str
    mbo_studio_id: str
    time_zone: str
    currency_code: str
    address: Address
    phone_number: str
    latitude: float
    longitude: float


class Coach(OtfBaseModel):
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
            return "90 min"
        return human_val

    @property
    def class_type(self) -> ClassType:
        for class_type in ClassType:
            if class_type.value in self.name:
                return class_type

        return ClassType.OTHER


class OtfClass(OtfBaseModel, OtfClassTimeMixin):
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
    def sidebar_data(self) -> Table:
        data = {
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


class OtfClassList(OtfBaseModel):
    classes: list[OtfClass]

    def _columns(self) -> list[dict[str, str]]:
        return [
            {"header": "Class DoW", "key": "day_of_week"},
            {"header": "Class Date", "key": "date"},
            {"header": "Class Time", "key": "time"},
            {"header": "Class Duration", "key": "duration"},
            {"header": "Class Name", "key": "name"},
            {"header": "Studio", "key": "studio.name"},
            {"header": "Home Studio", "key": "is_home_studio"},
            {"header": "Booked", "key": "is_booked"},
        ]

    def to_table(self) -> Table:
        table = Table(title="Classes", style="cyan")

        table.add_column("Class DoW")
        table.add_column("Class Date")
        table.add_column("Class Time")
        table.add_column("Class Duration")
        table.add_column("Class Name")
        table.add_column("Studio")
        table.add_column("Home Studio", justify="center")
        table.add_column("Booked", justify="center")

        home_studio_true = Styled("✓", style=Style(color="green"))
        home_studio_false = Styled("X", style="red")

        for otf_class in self.classes:
            home_studio = home_studio_true if otf_class.is_home_studio else home_studio_false

            table.add_row(
                otf_class.day_of_week,
                otf_class.date,
                otf_class.time,
                otf_class.duration,
                otf_class.name,
                otf_class.studio.name,
                home_studio,
                home_studio_true if otf_class.is_booked else "",
                style="green" if otf_class.is_booked else None,
            )

        return table
