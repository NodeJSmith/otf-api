from pydantic import BaseModel, Field


class ZoneTimeMinutes(BaseModel):
    gray: int
    blue: int
    green: int
    orange: int
    red: int


class HeartRate(BaseModel):
    max_hr: int
    peak_hr: int
    peak_hr_percent: int
    avg_hr: int
    avg_hr_percent: int


class PerformanceMetricFloat(BaseModel):
    display_value: float
    display_unit: str
    metric_value: float


class PerformanceMetricString(BaseModel):
    display_value: str
    display_unit: str
    metric_value: str


class BaseEquipment(BaseModel):
    avg_pace: PerformanceMetricString
    avg_speed: PerformanceMetricFloat
    max_pace: PerformanceMetricString
    max_speed: PerformanceMetricFloat
    moving_time: PerformanceMetricString
    total_distance: PerformanceMetricFloat


class Treadmill(BaseEquipment):
    avg_incline: PerformanceMetricFloat
    elevation_gained: PerformanceMetricFloat
    max_incline: PerformanceMetricFloat


class Rower(BaseEquipment):
    avg_cadence: PerformanceMetricFloat
    avg_power: PerformanceMetricFloat
    max_cadence: PerformanceMetricFloat


class EquipmentData(BaseModel):
    treadmill: Treadmill
    rower: Rower


class Details(BaseModel):
    calories_burned: int
    splat_points: int
    step_count: int
    active_time_seconds: int
    zone_time_minutes: ZoneTimeMinutes
    heart_rate: HeartRate
    equipment_data: EquipmentData


class Class(BaseModel):
    starts_at_local: str
    name: str


class PerformanceSummaryDetail(BaseModel):
    id: str
    details: Details
    ratable: bool
    otf_class: Class = Field(..., alias="class")
