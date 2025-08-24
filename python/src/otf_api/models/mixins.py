import typing
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator

if typing.TYPE_CHECKING:
    from otf_api.api.api import Otf


class ApiMixin:
    """Mixin for models that require an API instance to be set.

    This allows us to create model methods such as `cancel`, `book`, etc., that require an API instance to function.
    The API instance is set using the `set_api` method, and it can be accessed via the `_api` attribute.
    If the API instance is not set, calling methods that require it will raise a ValueError.
    """

    _api: "Otf" = None  # type: ignore[assignment]

    def set_api(self, api: "Otf") -> None:
        """Set the API instance for this model."""
        self._api = api

    @classmethod
    def create(cls, api: "Otf", **kwargs) -> typing.Self:
        """Creates a new instance of the model with the given keyword arguments."""
        instance = cls(**kwargs)
        if api is not None:
            instance.set_api(api)
        return instance

    def raise_if_api_not_set(self) -> None:
        """Raises an error if the API instance is not set."""
        if self._api is None:
            raise ValueError("API instance is not set. Use set_api() to set it before calling this method.")


class PhoneLongitudeLatitudeMixin:
    """Mixin for models that require phone number, latitude, and longitude fields.

    This mixin exists to make it easier to handle the various names these fields can have in different APIs.
    """

    phone_number: str | None = Field(None, validation_alias=AliasChoices("phone", "phoneNumber"))
    latitude: float | None = Field(None, validation_alias=AliasChoices("latitude"))
    longitude: float | None = Field(None, validation_alias=AliasChoices("longitude"))


class AddressMixin:
    """Mixin for models that require address fields.

    This mixin exists to make it easier to handle the various names these fields can have in different APIs.
    """

    address_line1: str | None = Field(
        None, validation_alias=AliasChoices("line1", "address1", "address", "physicalAddress")
    )
    address_line2: str | None = Field(None, validation_alias=AliasChoices("line2", "address2", "physicalAddress2"))
    city: str | None = Field(None, validation_alias=AliasChoices("city", "physicalCity", "suburb"))
    postal_code: str | None = Field(
        None, validation_alias=AliasChoices("postal_code", "postalCode", "physicalPostalCode")
    )
    state: str | None = Field(None, validation_alias=AliasChoices("state", "physicalState", "territory"))
    country: str | None = Field(None, validation_alias=AliasChoices("country", "physicalCountry"))
    region: str | None = Field(
        None, exclude=True, repr=False, validation_alias=AliasChoices("physicalRegion", "region")
    )
    country_id: int | None = Field(
        None, exclude=True, repr=False, validation_alias=AliasChoices("physicalCountryId", "countryId")
    )

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Any) -> Any:  # noqa: ANN401
        """Validates address fields and country format, handling specific cases."""
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
        """Clean strings by stripping whitespace and returning None if empty."""
        if value is None:
            return value
        value = value.strip()

        if not value:
            return None

        return value
