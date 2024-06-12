from pydantic import Field

from otf.models.base import OtfBaseModel


class MaxHr(OtfBaseModel):
    type: str
    value: int


class Zone(OtfBaseModel):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(OtfBaseModel):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class HistoryItem(OtfBaseModel):
    max_hr: MaxHr = Field(..., alias="maxHr")
    zones: Zones
    change_from_previous: int = Field(..., alias="changeFromPrevious")
    change_bucket: str = Field(..., alias="changeBucket")
    assigned_at: str = Field(..., alias="assignedAt")


class DnaHrHistory(OtfBaseModel):
    member_uuid: str = Field(..., alias="memberUuid")
    history: list[HistoryItem]
