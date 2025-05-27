from datetime import datetime, timedelta
from typing import Any

from pydantic import AliasPath, Field, field_serializer

from otf_api.models.base import OtfItemBase


class Zone(OtfItemBase):
    start_bpm: int = Field(..., validation_alias="startBpm")
    end_bpm: int = Field(..., validation_alias="endBpm")


class Zones(OtfItemBase):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class TreadData(OtfItemBase):
    tread_speed: float = Field(..., validation_alias="treadSpeed")
    tread_incline: float = Field(..., validation_alias="treadIncline")
    agg_tread_distance: int = Field(..., validation_alias="aggTreadDistance")


class RowData(OtfItemBase):
    row_speed: float = Field(..., validation_alias="rowSpeed")
    row_pps: float = Field(..., validation_alias="rowPps")
    row_spm: float = Field(..., validation_alias="rowSpm")
    agg_row_distance: int = Field(..., validation_alias="aggRowDistance")
    row_pace: int = Field(..., validation_alias="rowPace")


class TelemetryItem(OtfItemBase):
    relative_timestamp: int = Field(..., validation_alias="relativeTimestamp")
    hr: int | None = None
    agg_splats: int = Field(..., validation_alias="aggSplats")
    agg_calories: int = Field(..., validation_alias="aggCalories")
    timestamp: datetime | None = Field(
        None,
        init_var=False,
        description="The timestamp of the telemetry item, calculated from the class start time and relative timestamp.",
    )
    tread_data: TreadData | None = Field(None, validation_alias="treadData")
    row_data: RowData | None = Field(None, validation_alias="rowData")


class Telemetry(OtfItemBase):
    member_uuid: str = Field(..., validation_alias="memberUuid")
    performance_summary_id: str = Field(
        ...,
        validation_alias="classHistoryUuid",
        description="The ID of the performance summary this telemetry item belongs to.",
    )
    class_history_uuid: str = Field(
        ..., validation_alias="classHistoryUuid", description="The same as performance_summary_id."
    )
    class_start_time: datetime | None = Field(None, validation_alias="classStartTime")
    max_hr: int | None = Field(None, validation_alias="maxHr")
    zones: Zones
    window_size: int | None = Field(None, validation_alias="windowSize")
    telemetry: list[TelemetryItem] = Field(default_factory=list)

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)
        for telem in self.telemetry:
            if self.class_start_time is None:
                continue

            telem.timestamp = self.class_start_time + timedelta(seconds=telem.relative_timestamp)

    @field_serializer("telemetry", when_used="json")
    def reduce_telemetry_list(self, value: list[TelemetryItem]) -> list[TelemetryItem]:
        """Reduces the telemetry list to only include the first 10 items."""
        if len(value) > 10:
            return value[:5] + value[-5:]
        return value


class TelemetryHistoryItem(OtfItemBase):
    max_hr_type: str | None = Field(None, validation_alias=AliasPath("maxHr", "type"))
    max_hr_value: int | None = Field(None, validation_alias=AliasPath("maxHr", "value"))
    zones: Zones | None = None
    change_from_previous: int | None = Field(None, validation_alias="changeFromPrevious")
    change_bucket: str | None = Field(None, validation_alias="changeBucket")
    assigned_at: datetime | None = Field(None, validation_alias="assignedAt")
