"""
These models represent the data returned by the challenge tracker endpoint.

I believe these are used by the app to populate the list of challenges, programs,
and benchmarks that a member can compete in.

The actual data for *your* participation in these challenges is returned by a different
endpoint.
"""

from pydantic import Field

from otf_api.models.base import OtfItemBase
from otf_api.models.enums import ChallengeCategory, EquipmentType


class Year(OtfItemBase):
    year: int | None = Field(None, alias="Year")
    is_participated: bool | None = Field(None, alias="IsParticipated")
    in_progress: bool | None = Field(None, alias="InProgress")


class Program(OtfItemBase):
    """A program represents multi-day/week challenges that members can participate in."""

    # NOTE: These ones do seem to match the ChallengeType enums in the OTF app.
    # Leaving them as int for now though in case older data or other user's
    # data doesn't match up.
    challenge_category_id: int | None = Field(None, alias="ChallengeCategoryId")
    challenge_sub_category_id: int | None = Field(None, alias="ChallengeSubCategoryId")
    challenge_name: str | None = Field(None, alias="ChallengeName")
    years: list[Year] = Field(default_factory=list, alias="Years")


class Challenge(OtfItemBase):
    """A challenge represents a single day or event that members can participate in."""

    # NOTE: The challenge category/subcategory ids here do not seem to be at
    # all related to the ChallengeType enums or the few SubCategory enums I've
    # been able to puzzle out. I haven't been able to link them to any code
    # in the OTF app. Due to that, they are being excluded from the model for now.
    challenge_category_id: ChallengeCategory | None = Field(None, alias="ChallengeCategoryId")
    challenge_sub_category_id: int | None = Field(None, alias="ChallengeSubCategoryId")
    challenge_name: str | None = Field(None, alias="ChallengeName")
    years: list[Year] = Field(default_factory=list, alias="Years")


class Benchmark(OtfItemBase):
    """A benchmark represents a specific workout that members can participate in."""

    equipment_id: EquipmentType | None = Field(None, alias="EquipmentId")
    equipment_name: str | None = Field(None, alias="EquipmentName")
    years: list[Year] = Field(default_factory=list, alias="Years")


class ChallengeTracker(OtfItemBase):
    programs: list[Program] = Field(default_factory=list, alias="Programs")
    challenges: list[Challenge] = Field(default_factory=list, alias="Challenges")
    benchmarks: list[Benchmark] = Field(default_factory=list, alias="Benchmarks")
