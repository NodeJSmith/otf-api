from pydantic import Field

from otf_api.models.base import OtfItemBase

from .enums import EquipmentType


class Year(OtfItemBase):
    """A year entry indicating member participation in a challenge or benchmark."""

    year: int | None = Field(None, validation_alias="Year", description="The calendar year.")
    is_participated: bool | None = Field(
        None, validation_alias="IsParticipated", description="Whether the member participated this year."
    )
    in_progress: bool | None = Field(
        None, validation_alias="InProgress", description="Whether the challenge is currently in progress."
    )


class Program(OtfItemBase):
    """A program represents multi-day/week challenges that members can participate in.

    NOTE: The category/sub-category IDs appear to match the ChallengeType enums in the OTF app,
    but are kept as int rather than enum in case older data or other users' data doesn't match.
    """

    challenge_category_id: int | None = Field(
        None, validation_alias="ChallengeCategoryId", description="Category ID for the challenge program."
    )
    challenge_sub_category_id: int | None = Field(
        None, validation_alias="ChallengeSubCategoryId", description="Sub-category ID for the challenge program."
    )
    challenge_name: str | None = Field(
        None, validation_alias="ChallengeName", description="Display name of the challenge program."
    )
    years: list[Year] = Field(
        default_factory=list, validation_alias="Years", description="Years the member has participated."
    )


class Challenge(OtfItemBase):
    """A challenge represents a single day or event that members can participate in.

    NOTE: The challenge category/subcategory ids here do not seem to be related to the
    ChallengeType enums or SubCategory enums from the OTF app.
    """

    challenge_category_id: int | None = Field(
        None, validation_alias="ChallengeCategoryId", description="Category ID for the challenge."
    )
    challenge_sub_category_id: int | None = Field(
        None, validation_alias="ChallengeSubCategoryId", description="Sub-category ID for the challenge."
    )
    challenge_name: str | None = Field(
        None, validation_alias="ChallengeName", description="Display name of the challenge."
    )
    years: list[Year] = Field(
        default_factory=list, validation_alias="Years", description="Years the member has participated."
    )


class Benchmark(OtfItemBase):
    """A benchmark represents a specific workout that members can participate in."""

    equipment_id: EquipmentType | None = Field(
        None, validation_alias="EquipmentId", description="Type of equipment used for the benchmark."
    )
    equipment_name: str | None = Field(
        None, validation_alias="EquipmentName", description="Display name of the equipment."
    )
    years: list[Year] = Field(
        default_factory=list, validation_alias="Years", description="Years the member has participated."
    )


class ChallengeTracker(OtfItemBase):
    """Top-level container for all challenge, program, and benchmark participation data."""

    programs: list[Program] = Field(
        default_factory=list, validation_alias="Programs", description="Multi-day/week challenge programs."
    )
    challenges: list[Challenge] = Field(
        default_factory=list, validation_alias="Challenges", description="Single-day event challenges."
    )
    benchmarks: list[Benchmark] = Field(
        default_factory=list, validation_alias="Benchmarks", description="Benchmark workout records."
    )
