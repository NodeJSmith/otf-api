from datetime import datetime, timedelta
from typing import Any

from pydantic import Field

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
    class_history_uuid: str = Field(..., alias="classHistoryUuid")
    class_start_time: datetime = Field(..., alias="classStartTime")
    max_hr: int = Field(..., alias="maxHr")
    zones: Zones
    window_size: int = Field(..., alias="windowSize")
    telemetry: list[TelemetryItem]

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)
        for telem in self.telemetry:
            telem.timestamp = self.class_start_time + timedelta(seconds=telem.relative_timestamp)
