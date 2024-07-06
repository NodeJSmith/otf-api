from pydantic import Field

from otf_api.models.base import OtfItemBase


class MaxHr(OtfItemBase):
    type: str
    value: int


class TelemetryMaxHr(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUuid")
    max_hr: MaxHr = Field(..., alias="maxHr")
