from pydantic import Field

from otf_api.models.base import OtfItemBase


class Year(OtfItemBase):
    year: str = Field(..., alias="Year")
    is_participated: bool = Field(..., alias="IsParticipated")
    in_progress: bool = Field(..., alias="InProgress")


class Program(OtfItemBase):
    challenge_category_id: int = Field(..., alias="ChallengeCategoryId")
    challenge_sub_category_id: int = Field(..., alias="ChallengeSubCategoryId")
    challenge_name: str = Field(..., alias="ChallengeName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class Challenge(OtfItemBase):
    challenge_category_id: int = Field(..., alias="ChallengeCategoryId")
    challenge_sub_category_id: int = Field(..., alias="ChallengeSubCategoryId")
    challenge_name: str = Field(..., alias="ChallengeName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class Benchmark(OtfItemBase):
    equipment_id: int = Field(..., alias="EquipmentId")
    equipment_name: str = Field(..., alias="EquipmentName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class ChallengeTrackerContent(OtfItemBase):
    programs: list[Program] = Field(..., alias="Programs")
    challenges: list[Challenge] = Field(..., alias="Challenges")
    benchmarks: list[Benchmark] = Field(..., alias="Benchmarks")
