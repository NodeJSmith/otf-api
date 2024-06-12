from pydantic import Field

from otf.models.base import OtfBaseModel


class Year(OtfBaseModel):
    year: str = Field(..., alias="Year")
    is_participated: bool = Field(..., alias="IsParticipated")
    in_progress: bool = Field(..., alias="InProgress")


class Program(OtfBaseModel):
    challenge_category_id: int = Field(..., alias="ChallengeCategoryId")
    challenge_sub_category_id: int = Field(..., alias="ChallengeSubCategoryId")
    challenge_name: str = Field(..., alias="ChallengeName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class Challenge(OtfBaseModel):
    challenge_category_id: int = Field(..., alias="ChallengeCategoryId")
    challenge_sub_category_id: int = Field(..., alias="ChallengeSubCategoryId")
    challenge_name: str = Field(..., alias="ChallengeName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class Benchmark(OtfBaseModel):
    equipment_id: int = Field(..., alias="EquipmentId")
    equipment_name: str = Field(..., alias="EquipmentName")
    years: list[Year] = Field(..., alias="Years")
    logo_url: str = Field(..., alias="LogoUrl")


class ChallengeTrackerContent(OtfBaseModel):
    programs: list[Program] = Field(..., alias="Programs")
    challenges: list[Challenge] = Field(..., alias="Challenges")
    benchmarks: list[Benchmark] = Field(..., alias="Benchmarks")
