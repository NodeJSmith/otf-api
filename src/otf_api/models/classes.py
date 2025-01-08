from datetime import datetime

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import DoW
from otf_api.models.mixins import AddressMixin, OtfClassTimeMixin, PhoneLongitudeLatitudeMixin


class Studio(PhoneLongitudeLatitudeMixin, OtfItemBase):
    studio_uuid: str = Field(alias="id")
    name: str
    mbo_studio_id: str = Field(exclude=True)
    time_zone: str
    currency_code: str | None = None
    address: AddressMixin


class Coach(OtfItemBase):
    mbo_staff_id: str
    first_name: str
    image_url: str | None = None


class OtfClass(OtfItemBase, OtfClassTimeMixin):
    id: str
    class_uuid: str = Field(
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
    is_cancelled: bool = Field(alias="canceled")
    mbo_class_id: str
    mbo_class_schedule_id: str
    mbo_class_description_id: str
    created_at: datetime
    updated_at: datetime
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")
    is_booked: bool | None = Field(None, description="Custom helper field to determine if class is already booked")

    def __str__(self) -> str:
        starts_at_str = self.starts_at_local.strftime("%Y-%m-%d %H:%M:%S")
        coach_name = self.coach.first_name
        return f"{starts_at_str} {self.name} with {coach_name}"

    @property
    def has_availability(self) -> bool:
        return not self.full

    @property
    def day_of_week_enum(self) -> DoW:
        dow = self.starts_at_local.strftime("%A").upper()
        return DoW(dow)


class OtfClassList(OtfItemBase):
    classes: list[OtfClass]

    def __len__(self) -> int:
        return len(self.classes)

    def __iter__(self):
        return iter(self.classes)

    def __getitem__(self, item) -> OtfClass:
        return self.classes[item]
