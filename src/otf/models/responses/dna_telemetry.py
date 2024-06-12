from datetime import datetime, timedelta

from pydantic import Field

from otf.models.base import OtfBaseModel


class Zone(OtfBaseModel):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(OtfBaseModel):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class TreadData(OtfBaseModel):
    tread_speed: float = Field(..., alias="treadSpeed")
    tread_incline: float = Field(..., alias="treadIncline")
    agg_tread_distance: int = Field(..., alias="aggTreadDistance")


class TelemetryItem(OtfBaseModel):
    relative_timestamp: int = Field(..., alias="relativeTimestamp")
    hr: int
    agg_splats: int = Field(..., alias="aggSplats")
    agg_calories: int = Field(..., alias="aggCalories")
    timestamp: datetime | None = Field(
        None,
        init_var=False,
        description="The timestamp of the telemetry item, calculated from the class start time and relative timestamp.",
    )
    tread_data: TreadData | None = Field(None, alias="treadData")


class DnaTelemetry(OtfBaseModel):
    member_uuid: str = Field(..., alias="memberUuid")
    class_history_uuid: str = Field(..., alias="classHistoryUuid")
    class_start_time: datetime = Field(..., alias="classStartTime")
    max_hr: int = Field(..., alias="maxHr")
    zones: Zones
    window_size: int = Field(..., alias="windowSize")
    telemetry: list[TelemetryItem]

    def __init__(self, **data):
        super().__init__(**data)
        for telem in self.telemetry:
            telem.timestamp = self.class_start_time + timedelta(seconds=telem.relative_timestamp)
