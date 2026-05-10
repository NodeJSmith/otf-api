from datetime import datetime, timedelta

from pydantic import AliasPath, Field, field_serializer

from otf_api.models.base import OtfItemBase


class Zone(OtfItemBase):
    """A heart rate zone defined by a BPM range."""

    start_bpm: int = Field(..., validation_alias="startBpm", description="Lower bound BPM for this zone.")
    end_bpm: int = Field(..., validation_alias="endBpm", description="Upper bound BPM for this zone.")


class Zones(OtfItemBase):
    """The five OTF heart rate zones (gray, blue, green, orange, red) with their BPM ranges."""

    gray: Zone = Field(..., description="Rest/very light effort zone.")
    blue: Zone = Field(..., description="Light effort zone.")
    green: Zone = Field(..., description="Moderate effort (base pace) zone.")
    orange: Zone = Field(..., description="High effort (push pace) zone, earns splat points.")
    red: Zone = Field(..., description="Maximum effort (all-out) zone, earns splat points.")


class TreadData(OtfItemBase):
    """Treadmill telemetry data for a single point in time."""

    tread_speed: float = Field(..., validation_alias="treadSpeed", description="Current treadmill speed.")
    tread_incline: float = Field(..., validation_alias="treadIncline", description="Current treadmill incline.")
    agg_tread_distance: int = Field(
        ..., validation_alias="aggTreadDistance", description="Cumulative treadmill distance."
    )


class RowData(OtfItemBase):
    """Rower telemetry data for a single point in time."""

    row_speed: float = Field(..., validation_alias="rowSpeed", description="Current rowing speed.")
    row_pps: float = Field(..., validation_alias="rowPps", description="Rowing power per stroke.")
    row_spm: float = Field(..., validation_alias="rowSpm", description="Rowing strokes per minute.")
    agg_row_distance: int = Field(..., validation_alias="aggRowDistance", description="Cumulative rowing distance.")
    row_pace: int = Field(..., validation_alias="rowPace", description="Current rowing pace.")


class TelemetryItem(OtfItemBase):
    """A single telemetry data point captured during a workout."""

    relative_timestamp: int = Field(
        ..., validation_alias="relativeTimestamp", description="Seconds since the start of the class."
    )
    hr: int | None = Field(None, description="Heart rate in BPM at this point in time.")
    agg_splats: int = Field(..., validation_alias="aggSplats", description="Cumulative splat points at this time.")
    agg_calories: int = Field(
        ..., validation_alias="aggCalories", description="Cumulative calories burned at this time."
    )
    timestamp: datetime | None = Field(
        None,
        init_var=False,
        description="The timestamp of the telemetry item, calculated from the class start time and relative timestamp.",
    )
    tread_data: TreadData | None = Field(
        None, validation_alias="treadData", description="Treadmill data, present when on the treadmill."
    )
    row_data: RowData | None = Field(
        None, validation_alias="rowData", description="Rower data, present when on the rower."
    )


class Telemetry(OtfItemBase):
    """Full telemetry data for a workout, including time-series heart rate and equipment data."""

    member_uuid: str = Field(..., validation_alias="memberUuid", description="Unique identifier for the member.")
    performance_summary_id: str = Field(
        ...,
        validation_alias="classHistoryUuid",
        description="The ID of the performance summary this telemetry item belongs to.",
    )
    class_history_uuid: str = Field(
        ..., validation_alias="classHistoryUuid", description="The same as performance_summary_id."
    )
    class_start_time: datetime | None = Field(
        None, validation_alias="classStartTime", description="When the class started."
    )
    max_hr: int | None = Field(None, validation_alias="maxHr", description="Member's max heart rate.")
    zones: Zones | None = Field(default=None, description="The zones associated with the telemetry.")
    window_size: int | None = Field(
        None, validation_alias="windowSize", description="Telemetry sampling window size in seconds."
    )
    telemetry: list[TelemetryItem] = Field(default_factory=list, description="Time-series telemetry data points.")

    def model_post_init(self, __context: object) -> None:  # noqa: D102
        if self.class_start_time is None:
            return

        for telem in self.telemetry:
            telem.timestamp = self.class_start_time + timedelta(seconds=telem.relative_timestamp)

    @field_serializer("telemetry", when_used="json")
    def reduce_telemetry_list(self, value: list[TelemetryItem]) -> list[TelemetryItem]:
        """Reduces the telemetry list to first and last 5 items when serializing to JSON."""
        if len(value) > 10:
            return value[:5] + value[-5:]
        return value


class TelemetryHistoryItem(OtfItemBase):
    """A historical record of a member's max heart rate zone configuration changes."""

    max_hr_type: str | None = Field(
        None, validation_alias=AliasPath("maxHr", "type"), description="Method used to determine max HR."
    )
    max_hr_value: int | None = Field(
        None, validation_alias=AliasPath("maxHr", "value"), description="Max heart rate value."
    )
    zones: Zones | None = Field(None, description="Heart rate zone boundaries at this point in time.")
    change_from_previous: int | None = Field(
        None, validation_alias="changeFromPrevious", description="BPM change from the previous max HR value."
    )
    change_bucket: str | None = Field(
        None, validation_alias="changeBucket", description="Category of the change (e.g. increase, decrease)."
    )
    assigned_at: datetime | None = Field(
        None, validation_alias="assignedAt", description="When this max HR configuration was assigned."
    )
