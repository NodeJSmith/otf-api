from datetime import datetime

from pydantic import BaseModel


class Address(BaseModel):
    line1: str
    city: str
    state: str
    country: str
    postal_code: str


class Studio(BaseModel):
    id: str
    name: str
    mbo_studio_id: str
    time_zone: str
    currency_code: str
    address: Address
    phone_number: str
    latitude: float
    longitude: float


class Coach(BaseModel):
    mbo_staff_id: str
    first_name: str
    image_url: str | None = None


class OtfClass(BaseModel):
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


class OtfClassList(BaseModel):
    classes: list[OtfClass]
