from pydantic import Field

from otf_api.models.base import OtfItemBase


class MaxHr(OtfItemBase):
    type: str
    value: int


class Zone(OtfItemBase):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(OtfItemBase):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class HistoryItem(OtfItemBase):
    max_hr: MaxHr = Field(..., alias="maxHr")
    zones: Zones
    change_from_previous: int = Field(..., alias="changeFromPrevious")
    change_bucket: str = Field(..., alias="changeBucket")
    assigned_at: str = Field(..., alias="assignedAt")


class TelemetryHrHistory(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUuid")
    history: list[HistoryItem]
