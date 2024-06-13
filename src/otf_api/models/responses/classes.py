from datetime import datetime

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


class OtfClassList(OtfBaseModel):
    classes: list[OtfClass]
