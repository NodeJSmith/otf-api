import inspect
from datetime import datetime
from enum import Enum

import pint
from pydantic import BaseModel, Field, field_validator

from otf_api.models.base import OtfItemBase

ureg = pint.UnitRegistry()

DEFAULT_WEIGHT_DIVIDERS = [55.0, 70.0, 85.0, 100.0, 115.0, 130.0, 145.0, 160.0, 175.0, 190.0, 205.0]
DEFAULT_SKELETAL_MUSCLE_MASS_DIVIDERS = [70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0]
DEFAULT_BODY_FAT_MASS_DIVIDERS = [40.0, 60.0, 80.0, 100.0, 160.0, 220.0, 280.0, 340.0, 400.0, 460.0, 520.0]


class AverageType(str, Enum):
    BELOW_AVERAGE = "BELOW_AVERAGE"
    AVERAGE = "AVERAGE"
    ABOVE_AVERAGE = "ABOVE_AVERAGE"
    MINIMUM = "MINIMUM"  # unused


class BodyFatPercentIndicator(str, Enum):
    NO_INDICATOR = "NO_INDICATOR"
    MINIMUM_BODY_FAT = "MINIMUM_BODY_FAT"  # unused
    LOW_BODY_FAT = "LOW_BODY_FAT"  # unused
    HEALTHY_BODY_FAT = "HEALTHY_BODY_FAT"
    GOAL_SETTING_FAT = "GOAL_SETTING_FAT"
    HIGH_BODY_FAT = "HIGH_BODY_FAT"
    OBESE_BODY_FAT = "OBESE_BODY_FAT"  # unused


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"


def get_percent_body_fat_descriptor(
    percent_body_fat: float, body_fat_percent_dividers: list[float]
) -> BodyFatPercentIndicator:
    if not percent_body_fat or not body_fat_percent_dividers[3]:
        return BodyFatPercentIndicator.NO_INDICATOR

    if percent_body_fat < body_fat_percent_dividers[1]:
        return BodyFatPercentIndicator.HEALTHY_BODY_FAT

    if percent_body_fat < body_fat_percent_dividers[2]:
        return BodyFatPercentIndicator.GOAL_SETTING_FAT

    return BodyFatPercentIndicator.HIGH_BODY_FAT


def get_relative_descriptor(in_body_value: float, in_body_dividers: list[float]) -> AverageType:
    if in_body_value <= in_body_dividers[2]:
        return AverageType.BELOW_AVERAGE

    if in_body_value <= in_body_dividers[4]:
        return AverageType.AVERAGE

    return AverageType.ABOVE_AVERAGE


def get_body_fat_percent_dividers(age: int, gender: Gender) -> list[float]:
    if gender == Gender.MALE:
        return get_body_fat_percent_dividers_male(age)

    return get_body_fat_percent_dividers_female(age)


def get_body_fat_percent_dividers_male(age: int) -> list[float]:
    match age:
        case age if 0 <= age < 30:
            return [0.0, 13.1, 21.1, 100.0]
        case age if 30 <= age < 40:
            return [0.0, 17.1, 23.1, 100.0]
        case age if 40 <= age < 50:
            return [0.0, 20.1, 25.1, 100.0]
        case age if 50 <= age < 60:
            return [0.0, 21.1, 26.1, 100.0]
        case age if 60 <= age < 70:
            return [0.0, 22.1, 27.1, 100.0]
        case _:
            return [0.0, 0.0, 0.0, 0.0]


def get_body_fat_percent_dividers_female(age: int) -> list[float]:
    match age:
        case age if 0 <= age < 30:
            return [0.0, 19.1, 26.1, 100.0]
        case age if 30 <= age < 40:
            return [0.0, 20.1, 27.1, 100.0]
        case age if 40 <= age < 50:
            return [0.0, 22.1, 30.1, 100.0]
        case age if 50 <= age < 60:
            return [0.0, 25.1, 32.1, 100.0]
        case age if 60 <= age < 70:
            return [0.0, 26.1, 33.1, 100.0]
        case _:
            return [0.0, 0.0, 0.0, 0.0]


class LeanBodyMass(OtfItemBase):
    left_arm: float = Field(..., alias="lbmOfLeftArm")
    left_leg: float = Field(..., alias="lbmOfLeftLeg")
    right_arm: float = Field(..., alias="lbmOfRightArm")
    right_leg: float = Field(..., alias="lbmOfRightLeg")
    trunk: float = Field(..., alias="lbmOfTrunk")


class LeanBodyMassPercent(OtfItemBase):
    left_arm: float = Field(..., alias="lbmPercentOfLeftArm")
    left_leg: float = Field(..., alias="lbmPercentOfLeftLeg")
    right_arm: float = Field(..., alias="lbmPercentOfRightArm")
    right_leg: float = Field(..., alias="lbmPercentOfRightLeg")
    trunk: float = Field(..., alias="lbmPercentOfTrunk")


class BodyFatMass(OtfItemBase):
    control: float = Field(..., alias="bfmControl")
    left_arm: float = Field(..., alias="bfmOfLeftArm")
    left_leg: float = Field(..., alias="bfmOfLeftLeg")
    right_arm: float = Field(..., alias="bfmOfRightArm")
    right_leg: float = Field(..., alias="bfmOfRightLeg")
    trunk: float = Field(..., alias="bfmOfTrunk")


class BodyFatMassPercent(OtfItemBase):
    left_arm: float = Field(..., alias="bfmPercentOfLeftArm")
    left_leg: float = Field(..., alias="bfmPercentOfLeftLeg")
    right_arm: float = Field(..., alias="bfmPercentOfRightArm")
    right_leg: float = Field(..., alias="bfmPercentOfRightLeg")
    trunk: float = Field(..., alias="bfmPercentOfTrunk")


class TotalBodyWeight(OtfItemBase):
    right_arm: float = Field(..., alias="tbwOfRightArm")
    left_arm: float = Field(..., alias="tbwOfLeftArm")
    trunk: float = Field(..., alias="tbwOfTrunk")
    right_leg: float = Field(..., alias="tbwOfRightLeg")
    left_leg: float = Field(..., alias="tbwOfLeftLeg")


class IntraCellularWater(OtfItemBase):
    right_arm: float = Field(..., alias="icwOfRightArm")
    left_arm: float = Field(..., alias="icwOfLeftArm")
    trunk: float = Field(..., alias="icwOfTrunk")
    right_leg: float = Field(..., alias="icwOfRightLeg")
    left_leg: float = Field(..., alias="icwOfLeftLeg")


class ExtraCellularWater(OtfItemBase):
    right_arm: float = Field(..., alias="ecwOfRightArm")
    left_arm: float = Field(..., alias="ecwOfLeftArm")
    trunk: float = Field(..., alias="ecwOfTrunk")
    right_leg: float = Field(..., alias="ecwOfRightLeg")
    left_leg: float = Field(..., alias="ecwOfLeftLeg")


class ExtraCellularWaterOverTotalBodyWater(OtfItemBase):
    right_arm: float = Field(..., alias="ecwOverTBWOfRightArm")
    left_arm: float = Field(..., alias="ecwOverTBWOfLeftArm")
    trunk: float = Field(..., alias="ecwOverTBWOfTrunk")
    right_leg: float = Field(..., alias="ecwOverTBWOfRightLeg")
    left_leg: float = Field(..., alias="ecwOverTBWOfLeftLeg")


class BodyCompositionData(OtfItemBase):
    member_uuid: str = Field(..., alias="memberUUId")
    member_id: str = Field(..., alias="memberId")
    scan_result_uuid: str = Field(..., alias="scanResultUUId")
    inbody_id: str = Field(..., alias="id", exclude=True, description="InBody ID, same as email address")
    email: str
    height: str = Field(..., description="Height in cm")
    gender: Gender
    age: int
    scan_datetime: datetime = Field(..., alias="testDatetime")
    provided_weight: float = Field(
        ..., alias="weight", description="Weight in pounds, provided by member at time of scan"
    )

    lean_body_mass_details: LeanBodyMass
    lean_body_mass_percent_details: LeanBodyMassPercent

    total_body_weight: float = Field(..., alias="tbw", description="Total body weight in pounds, based on scan results")
    dry_lean_mass: float = Field(..., alias="dlm")
    body_fat_mass: float = Field(..., alias="bfm")
    lean_body_mass: float = Field(..., alias="lbm")
    skeletal_muscle_mass: float = Field(..., alias="smm")
    body_mass_index: float = Field(..., alias="bmi")
    percent_body_fat: float = Field(..., alias="pbf")
    basal_metabolic_rate: float = Field(..., alias="bmr")
    in_body_type: str = Field(..., alias="inBodyType")

    # excluded because they are only useful for end result of calculations
    body_fat_mass_dividers: list[float] = Field(..., alias="bfmGraphScale", exclude=True)
    body_fat_mass_plot_point: float = Field(..., alias="pfatnew", exclude=True)
    skeletal_muscle_mass_dividers: list[float] = Field(..., alias="smmGraphScale", exclude=True)
    skeletal_muscle_mass_plot_point: float = Field(..., alias="psmm", exclude=True)
    weight_dividers: list[float] = Field(..., alias="wtGraphScale", exclude=True)
    weight_plot_point: float = Field(..., alias="pwt", exclude=True)

    # excluded due to 0 values
    body_fat_mass_details: BodyFatMass = Field(..., exclude=True)
    body_fat_mass_percent_details: BodyFatMassPercent = Field(..., exclude=True)
    total_body_weight_details: TotalBodyWeight = Field(..., exclude=True)
    intra_cellular_water_details: IntraCellularWater = Field(..., exclude=True)
    extra_cellular_water_details: ExtraCellularWater = Field(..., exclude=True)
    extra_cellular_water_over_total_body_water_details: ExtraCellularWaterOverTotalBodyWater = Field(..., exclude=True)
    visceral_fat_level: float = Field(..., alias="vfl", exclude=True)
    visceral_fat_area: float = Field(..., alias="vfa", exclude=True)
    body_comp_measurement: float = Field(..., alias="bcm", exclude=True)
    total_body_weight_over_lean_body_mass: float = Field(..., alias="tbwOverLBM", exclude=True)
    intracellular_water: float = Field(..., alias="icw", exclude=True)
    extracellular_water: float = Field(..., alias="ecw", exclude=True)
    lean_body_mass_control: float = Field(..., alias="lbmControl", exclude=True)

    def __init__(self, **data):
        # populate child models
        child_model_dict = {
            k: v.annotation
            for k, v in self.model_fields.items()
            if inspect.isclass(v.annotation) and issubclass(v.annotation, BaseModel)
        }
        for k, v in child_model_dict.items():
            data[k] = v(**data)

        super().__init__(**data)

    @field_validator("member_id", mode="before")
    @classmethod
    def int_to_str(cls, v: int):
        return str(v)

    @field_validator("skeletal_muscle_mass_dividers", "weight_dividers", "body_fat_mass_dividers", mode="before")
    @classmethod
    def convert_dividers_to_float_list(cls, v: str):
        return [float(i) for i in v.split(";")]

    @field_validator("total_body_weight", mode="before")
    @classmethod
    def convert_body_weight_from_kg_to_pounds(cls, v: float):
        return ureg.Quantity(v, ureg.kilogram).to(ureg.pound).magnitude

    @property
    def body_fat_mass_relative_descriptor(self) -> AverageType:
        """Get the relative descriptor for the body fat mass plot point.

        For this item, a lower value is better.

        Returns:
            AverageType: The relative descriptor for the body fat mass plot point
        """
        dividers = self.body_fat_mass_dividers or DEFAULT_BODY_FAT_MASS_DIVIDERS
        return get_relative_descriptor(self.body_fat_mass_plot_point, dividers)

    @property
    def skeletal_muscle_mass_relative_descriptor(self) -> AverageType:
        """Get the relative descriptor for the skeletal muscle mass plot point.

        For this item, a higher value is better.

        Returns:
            AverageType: The relative descriptor for the skeletal muscle mass plot point

        """
        dividers = self.skeletal_muscle_mass_dividers or DEFAULT_SKELETAL_MUSCLE_MASS_DIVIDERS
        return get_relative_descriptor(self.skeletal_muscle_mass_plot_point, dividers)

    @property
    def weight_relative_descriptor(self) -> AverageType:
        """Get the relative descriptor for the weight plot point.

        For this item, a lower value is better.

        Returns:
            AverageType: The relative descriptor for the weight
        """
        dividers = self.weight_dividers or DEFAULT_WEIGHT_DIVIDERS
        return get_relative_descriptor(self.weight_plot_point, dividers)

    @property
    def body_fat_percent_relative_descriptor(self) -> BodyFatPercentIndicator:
        """Get the relative descriptor for the percent body fat.

        Returns:
            BodyFatPercentIndicator: The relative descriptor for the percent body fat
        """
        return get_percent_body_fat_descriptor(
            self.percent_body_fat, get_body_fat_percent_dividers(self.age, self.gender)
        )


class BodyCompositionList(OtfItemBase):
    data: list[BodyCompositionData]
