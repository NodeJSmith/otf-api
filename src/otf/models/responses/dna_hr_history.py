from pydantic import BaseModel, Field


class MaxHr(BaseModel):
    type: str
    value: int


class Zone(BaseModel):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(BaseModel):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class HistoryItem(BaseModel):
    max_hr: MaxHr = Field(..., alias="maxHr")
    zones: Zones
    change_from_previous: int = Field(..., alias="changeFromPrevious")
    change_bucket: str = Field(..., alias="changeBucket")
    assigned_at: str = Field(..., alias="assignedAt")


class DnaHrHistory(BaseModel):
    member_uuid: str = Field(..., alias="memberUuid")
    history: list[HistoryItem]
