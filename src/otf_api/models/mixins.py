from pydantic import AliasChoices, Field, field_validator, model_validator

from otf_api.models.base import OtfItemBase


class PhoneLongitudeLatitudeMixin(OtfItemBase):
    phone_number: str | None = Field(None, alias=AliasChoices("phone", "phoneNumber"))
    latitude: float | None = Field(None, alias=AliasChoices("latitude"))
    longitude: float | None = Field(None, alias=AliasChoices("longitude"))


class AddressMixin(OtfItemBase):
    address_line1: str | None = Field(None, alias=AliasChoices("line1", "address1", "address", "physicalAddress"))
    address_line2: str | None = Field(None, alias=AliasChoices("line2", "address2", "physicalAddress2"))
    city: str | None = Field(None, alias=AliasChoices("city", "physicalCity", "suburb"))
    postal_code: str | None = Field(None, alias=AliasChoices("postal_code", "postalCode", "physicalPostalCode"))
    state: str | None = Field(None, alias=AliasChoices("state", "physicalState", "territory"))
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

    @field_validator("address_line1", "address_line2", "city", "postal_code", "state", "country")
    @classmethod
    def clean_strings(cls, value: str | None, **_kwargs) -> str | None:
        if value is None:
            return value
        value = value.strip()

        if not value:
            return None

        return value
