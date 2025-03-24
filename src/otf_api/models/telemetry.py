from datetime import datetime, timedelta
from typing import Any

from pydantic import AliasPath, Field

from otf_api.models.base import OtfItemBase


class Zone(OtfItemBase):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(OtfItemBase):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class TreadData(OtfItemBase):
    tread_speed: float = Field(..., alias="treadSpeed")
    tread_incline: float = Field(..., alias="treadIncline")
    agg_tread_distance: int = Field(..., alias="aggTreadDistance")


class RowData(OtfItemBase):
    row_speed: float = Field(..., alias="rowSpeed")
    row_pps: float = Field(..., alias="rowPps")
    row_spm: float = Field(..., alias="rowSpm")
    agg_row_distance: int = Field(..., alias="aggRowDistance")
    row_pace: int = Field(..., alias="rowPace")


class TelemetryItem(OtfItemBase):
    relative_timestamp: int = Field(..., alias="relativeTimestamp")
    hr: int | None = None
    agg_splats: int = Field(..., alias="aggSplats")
    agg_calories: int = Field(..., alias="aggCalories")
    timestamp: datetime | None = Field(
        None,
        init_var=False,
        description="The timestamp of the telemetry item, calculated from the class start time and relative timestamp.",
    )
    tread_data: TreadData | None = Field(None, alias="treadData")
    row_data: RowData | None = Field(None, alias="rowData")


class Telemetry(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUuid")
    performance_summary_id: str = Field(
        ..., alias="classHistoryUuid", description="The ID of the performance summary this telemetry item belongs to."
    )
    class_history_uuid: str = Field(..., alias="classHistoryUuid", description="The same as performance_summary_id.")
    class_start_time: datetime | None = Field(None, alias="classStartTime")
    max_hr: int | None = Field(None, alias="maxHr")
    zones: Zones
    window_size: int | None = Field(None, alias="windowSize")
    telemetry: list[TelemetryItem] = Field(default_factory=list)

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)
        for telem in self.telemetry:
            telem.timestamp = self.class_start_time + timedelta(seconds=telem.relative_timestamp)


class TelemetryHistoryItem(OtfItemBase):
    max_hr_type: str | None = Field(None, alias=AliasPath("maxHr", "type"))
    max_hr_value: int | None = Field(None, alias=AliasPath("maxHr", "value"))
    zones: Zones | None = None
    change_from_previous: int | None = Field(None, alias="changeFromPrevious")
    change_bucket: str | None = Field(None, alias="changeBucket")
    assigned_at: datetime | None = Field(None, alias="assignedAt")
