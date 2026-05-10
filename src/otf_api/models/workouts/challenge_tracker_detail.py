from datetime import datetime
from typing import Any

from pydantic import Field

from otf_api.models.base import OtfItemBase

from .enums import EquipmentType


class MetricEntry(OtfItemBase):
    """Definition of a metric used to track benchmark performance."""

    title: str | None = Field(None, validation_alias="Title", description="Display title for the metric.")
    equipment_id: EquipmentType | None = Field(
        None, validation_alias="EquipmentId", description="Type of equipment for this metric."
    )
    entry_type: str | None = Field(
        None, validation_alias="EntryType", description="Type of entry (e.g. time, distance)."
    )
    metric_key: str | None = Field(None, validation_alias="MetricKey", description="Internal key for the metric.")
    min_value: str | None = Field(None, validation_alias="MinValue", description="Minimum valid value for this metric.")
    max_value: str | None = Field(None, validation_alias="MaxValue", description="Maximum valid value for this metric.")


class BenchmarkHistory(OtfItemBase):
    """A single benchmark result from a specific class."""

    studio_name: str | None = Field(
        None, validation_alias="StudioName", description="Name of the studio where the benchmark was performed."
    )
    equipment_id: EquipmentType | None = Field(
        None, validation_alias="EquipmentId", description="Type of equipment used."
    )
    class_time: datetime | None = Field(None, validation_alias="ClassTime", description="When the class took place.")
    challenge_sub_category_id: int | None = Field(
        None, validation_alias="ChallengeSubCategoryId", description="Sub-category of the benchmark."
    )
    weight_lbs: int | None = Field(
        None, validation_alias="WeightLBS", description="Member's weight in pounds at time of benchmark."
    )
    class_name: str | None = Field(None, validation_alias="ClassName", description="Name of the class.")
    coach_name: str | None = Field(None, validation_alias="CoachName", description="Name of the coach.")
    result: float | str | None = Field(
        None, validation_alias="Result", description="The benchmark result (time, distance, etc.)."
    )
    workout_type_id: int | None = Field(None, validation_alias="WorkoutTypeId", exclude=True, repr=False)
    workout_id: int | None = Field(None, validation_alias="WorkoutId", exclude=True, repr=False)
    linked_challenges: list[Any] | None = Field(None, validation_alias="LinkedChallenges", exclude=True, repr=False)

    date_created: datetime | None = Field(
        None,
        validation_alias="DateCreated",
        exclude=True,
        repr=False,
        description="When the entry was created in database, not useful to users",
    )
    date_updated: datetime | None = Field(
        None,
        validation_alias="DateUpdated",
        exclude=True,
        repr=False,
        description="When the entry was updated in database, not useful to users",
    )
    class_id: int | None = Field(
        None, validation_alias="ClassId", exclude=True, repr=False, description="Not used by API"
    )
    substitute_id: int | None = Field(
        None,
        validation_alias="SubstituteId",
        exclude=True,
        repr=False,
        description="Not used by API, also always seems to be 0",
    )


class ChallengeHistory(OtfItemBase):
    """A challenge participation record with benchmark results."""

    studio_name: str | None = Field(None, validation_alias="StudioName", description="Name of the studio.")
    start_date: datetime | None = Field(None, validation_alias="StartDate", description="Start date of the challenge.")
    end_date: datetime | None = Field(None, validation_alias="EndDate", description="End date of the challenge.")
    total_result: float | str | None = Field(
        None, validation_alias="TotalResult", description="Aggregated result for the challenge."
    )
    is_finished: bool | None = Field(
        None, validation_alias="IsFinished", description="Whether the challenge has been completed."
    )
    benchmark_histories: list[BenchmarkHistory] = Field(
        default_factory=list,
        validation_alias="BenchmarkHistories",
        description="Individual benchmark results within this challenge.",
    )

    challenge_id: int | None = Field(
        None, validation_alias="ChallengeId", exclude=True, repr=False, description="Not used by API"
    )
    studio_id: int | None = Field(
        None, validation_alias="StudioId", exclude=True, repr=False, description="Not used by API"
    )
    challenge_objective: str | None = Field(
        None, validation_alias="ChallengeObjective", exclude=True, repr=False, description="Always the string 'None'"
    )


class Goal(OtfItemBase):
    """Goal settings for a fitness benchmark."""

    goal: int | None = Field(None, validation_alias="Goal", description="Target value for the goal.")
    goal_period: str | None = Field(None, validation_alias="GoalPeriod", description="Time period for the goal.")
    overall_goal: int | None = Field(None, validation_alias="OverallGoal", description="Overall target value.")
    overall_goal_period: str | None = Field(
        None, validation_alias="OverallGoalPeriod", description="Time period for the overall goal."
    )
    min_overall: int | None = Field(None, validation_alias="MinOverall", description="Minimum overall value.")
    min_overall_period: str | None = Field(
        None, validation_alias="MinOverallPeriod", description="Time period for the minimum overall."
    )


class FitnessBenchmark(OtfItemBase):
    """Detailed benchmark data including history, records, and goals."""

    challenge_category_id: int | None = Field(
        None, validation_alias="ChallengeCategoryId", description="Category ID for the benchmark."
    )
    challenge_sub_category_id: int | None = Field(
        None, validation_alias="ChallengeSubCategoryId", description="Sub-category ID for the benchmark."
    )
    equipment_id: EquipmentType | None = Field(
        None, validation_alias="EquipmentId", description="Type of equipment used."
    )
    equipment_name: str | None = Field(
        None, validation_alias="EquipmentName", description="Display name of the equipment."
    )
    metric_entry: MetricEntry | None = Field(
        None, validation_alias="MetricEntry", description="Definition of the metric being tracked."
    )
    challenge_name: str | None = Field(
        None, validation_alias="ChallengeName", description="Display name of the benchmark."
    )
    best_record: float | str | None = Field(
        None, validation_alias="BestRecord", description="Member's all-time best result."
    )
    last_record: float | str | None = Field(
        None, validation_alias="LastRecord", description="Member's most recent result."
    )
    previous_record: float | str | None = Field(
        None, validation_alias="PreviousRecord", description="Member's previous result before the most recent."
    )
    unit: str | None = Field(None, validation_alias="Unit", description="Unit of measurement for the result.")
    goals: Goal | None = Field(None, validation_alias="Goals", description="Goal settings for this benchmark.")
    challenge_histories: list[ChallengeHistory] = Field(
        default_factory=list,
        validation_alias="ChallengeHistories",
        description="Historical participation records.",
    )
