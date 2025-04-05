from datetime import datetime

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ClassType, DoW
from otf_api.models.studio_detail import StudioDetail


class OtfClass(OtfItemBase):
    class_uuid: str = Field(alias="ot_base_class_uuid", description="The OTF class UUID")
    name: str | None = Field(None, description="The name of the class")
    class_type: ClassType = Field(alias="type")
    coach: str | None = Field(None, alias=AliasPath("coach", "first_name"))
    ends_at: datetime = Field(
        alias="ends_at_local",
        description="The end time of the class. Reflects local time, but the object does not have a timezone.",
    )
    starts_at: datetime = Field(
        alias="starts_at_local",
        description="The start time of the class. Reflects local time, but the object does not have a timezone.",
    )
    studio: StudioDetail

    # capacity/status fields
    booking_capacity: int | None = None
    full: bool | None = None
    max_capacity: int | None = None
    waitlist_available: bool | None = None
    waitlist_size: int | None = None
    is_booked: bool | None = Field(None, description="Custom helper field to determine if class is already booked")
    is_cancelled: bool | None = Field(None, alias="canceled")
    is_home_studio: bool | None = Field(None, description="Custom helper field to determine if at home studio")

    # unused fields
    class_id: str | None = Field(
        None, alias="id", exclude=True, repr=False, description="Matches new booking endpoint class id"
    )

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
