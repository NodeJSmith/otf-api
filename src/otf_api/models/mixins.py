from datetime import datetime

from humanize import precisedelta
from pydantic import AliasChoices, Field, model_validator

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ClassType


class PhoneLongitudeLatitudeMixin(OtfItemBase):
    phone_number: str | None = Field(None, alias=AliasChoices("phone", "phoneNumber"))
    latitude: float | None = Field(None, alias=AliasChoices("latitude"))
    longitude: float | None = Field(None, alias=AliasChoices("longitude"))


class AddressMixin(OtfItemBase):
    address_line1: str = Field(None, alias=AliasChoices("line1", "address1", "address", "physicalAddress"))
    address_line2: str | None = Field(None, alias=AliasChoices("line2", "address2", "physicalAddress2"))
    city: str | None = Field(None, alias=AliasChoices("city", "physicalCity"))
    postal_code: str | None = Field(None, alias=AliasChoices("postal_code", "postalCode", "physicalPostalCode"))
    state: str | None = Field(None, alias=AliasChoices("state", "physicalState"))
    country: str | None = Field(None, alias=AliasChoices("country", "physicalCountry"))
    region: str | None = Field(None, exclude=True, repr=False, alias=AliasChoices("physicalRegion", "region"))
    country_id: int | None = Field(None, exclude=True, repr=False, alias=AliasChoices("physicalCountryId", "countryId"))

    @model_validator(mode="before")
    @classmethod
    def check_country(cls, values):
        if set(values.keys()) == set(
            ["phone", "latitude", "longitude", "address1", "address2", "city", "state", "postalCode"]
        ):
            values = {k: v for k, v in values.items() if v and str(v) != "0.00000000"}

        if "country" in values and isinstance(values["country"], dict):
            values["country_currency"] = values.pop("country")

        if "physicalCountry" in values and isinstance(values["physicalCountry"], dict):
            values["country_currency"] = values.pop("physicalCountry")

        return values


class OtfClassTimeMixin:
    starts_at_local: datetime
    ends_at_local: datetime
    name: str

    @property
    def day_of_week(self) -> str:
        return self.starts_at_local.strftime("%A")

    @property
    def duration_str(self) -> str:
        """Returns the duration of the class in human readable format"""
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
