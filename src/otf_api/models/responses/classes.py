from datetime import datetime

from pydantic import Field
from rich.style import Style
from rich.styled import Styled
from rich.table import Table

from otf_api.models.base import OtfBaseModel


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


class OtfClass(OtfBaseModel):
    id: str
    ot_base_class_uuid: str
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


class OtfClassList(OtfBaseModel):
    classes: list[OtfClass]

    def to_table(self) -> Table:
        table = Table(title="Classes", style="cyan")

        table.add_column("Class Date")
        table.add_column("Class Name")
        table.add_column("Studio")
        table.add_column("Home Studio", justify="center")
        table.add_column("Class UUID")

        home_studio_true = Styled("✓", style=Style(color="green"))
        home_studio_false = Styled("X", style="red")

        for otf_class in self.classes:
            home_studio = home_studio_true if otf_class.is_home_studio else home_studio_false

            table.add_row(
                otf_class.starts_at_local.strftime("%Y-%m-%d %H:%M"),
                otf_class.name,
                otf_class.studio.name,
                home_studio,
                otf_class.ot_base_class_uuid,
            )

        return table
