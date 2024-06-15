from pydantic import Field

from otf_api.models.base import OtfBaseModel


class MaxHr(OtfBaseModel):
    type: str
    value: int


class TelemetryMaxHr(OtfBaseModel):
    member_uuid: str = Field(..., alias="memberUuid")
    max_hr: MaxHr = Field(..., alias="maxHr")
