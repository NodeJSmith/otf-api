from pydantic import Field

from otf_api.models.base import OtfItemBase


class TotalClasses(OtfItemBase):
    total_in_studio_classes_attended: int = Field(..., alias="totalInStudioClassesAttended")
    total_otlive_classes_attended: int = Field(..., alias="totalOtliveClassesAttended")
