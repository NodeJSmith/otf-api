from datetime import datetime, timedelta

from pydantic import BaseModel, Field


class Zone(BaseModel):
    start_bpm: int = Field(..., alias="startBpm")
    end_bpm: int = Field(..., alias="endBpm")


class Zones(BaseModel):
    gray: Zone
    blue: Zone
    green: Zone
    orange: Zone
    red: Zone


class TelemetryItem(BaseModel):
    relative_timestamp: int = Field(..., alias="relativeTimestamp")
    hr: int
    agg_splats: int = Field(..., alias="aggSplats")
    agg_calories: int = Field(..., alias="aggCalories")
    timestamp: datetime | None = Field(
        None,
        init_var=False,
        description="The timestamp of the telemetry item, calculated from the class start time and relative timestamp.",
    )


class DnaTelemetry(BaseModel):
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
