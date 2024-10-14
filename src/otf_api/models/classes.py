from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import DoW
from otf_api.models.mixins import OtfClassTimeMixin


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

    @property
    def actual_class_uuid(self) -> str:
        """The UUID used to book the class"""
        return self.ot_class_uuid


class OtfClassList(OtfItemBase):
    classes: list[OtfClass]
