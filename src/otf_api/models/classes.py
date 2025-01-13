from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ClassType, DoW
from otf_api.models.mixins import AddressMixin, PhoneLongitudeLatitudeMixin


class Studio(PhoneLongitudeLatitudeMixin, OtfItemBase):
    studio_uuid: str = Field(alias="id", description="The OTF studio UUID")
    name: str
    time_zone: str
    currency_code: str | None = None
    address: AddressMixin

    # unused fields
    mbo_studio_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")


class OtfClass(OtfItemBase):
    class_uuid: str = Field(alias="ot_base_class_uuid", description="The OTF class UUID")
    coach: str | None = Field(None, alias=AliasPath("coach", "first_name"))
    ends_at: datetime = Field(
        alias="ends_at_local",
        description="The end time of the class. Reflects local time, but the object does not have a timezone.",
    )
    name: str | None = Field(None, description="The name of the class")
    starts_at: datetime = Field(
        alias="starts_at_local",
        description="The start time of the class. Reflects local time, but the object does not have a timezone.",
    )
    studio: Studio
    class_type: ClassType = Field(alias="type")

    # capacity/status fields
    booking_capacity: int
    full: bool
    is_booked: bool | None = Field(None, description="Custom helper field to determine if class is already booked")
    is_cancelled: bool = Field(alias="canceled")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")
    max_capacity: int
    waitlist_available: bool
    waitlist_size: int

    # unused fields
    class_id: str | None = Field(None, alias="id", exclude=True, repr=False, description="Not used by API")

    created_at: datetime | None = Field(None, exclude=True, repr=False)
    ends_at_utc: datetime | None = Field(None, alias="ends_at", exclude=True, repr=False)
    mbo_class_description_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    mbo_class_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    mbo_class_schedule_id: str | None = Field(None, exclude=True, repr=False, description="MindBody attr")
    starts_at_utc: datetime | None = Field(None, alias="starts_at", exclude=True, repr=False)
    updated_at: datetime | None = Field(None, exclude=True, repr=False)

    @property
    def day_of_week(self) -> DoW:
        dow = self.starts_at.strftime("%A")
        return DoW(dow)

    @property
    def starts_at_local(self) -> datetime:
        """Alias for starts_at, kept to avoid breaking changes"""
        return self.starts_at

    @property
    def ends_at_local(self) -> datetime:
        """Alias for ends_at, kept to avoid breaking changes"""
        return self.ends_at

    def __str__(self) -> str:
        starts_at_str = self.starts_at.strftime("%a %b %d, %I:%M %p")
        booked_str = ""
        if self.is_booked:
            booked_str = "Booked"
        elif self.has_availability:
            booked_str = "Available"
        elif self.waitlist_available:
            booked_str = "Waitlist Available"
        else:
            booked_str = "Full"
        return f"Class: {starts_at_str} {self.name} - {self.coach} ({booked_str})"

    @property
    def has_availability(self) -> bool:
        return not self.full

    @property
    def day_of_week_enum(self) -> DoW:
        dow = self.starts_at.strftime("%A").upper()
        return DoW(dow)


class OtfClassList(OtfItemBase):
    classes: list[OtfClass]

    def __len__(self) -> int:
        return len(self.classes)

    def __iter__(self):
        return iter(self.classes)

    def __getitem__(self, item) -> OtfClass:
        return self.classes[item]
