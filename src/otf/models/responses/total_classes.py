from pydantic import Field

from otf.models.base import OtfBaseModel


class TotalClasses(OtfBaseModel):
    total_in_studio_classes_attended: int = Field(..., alias="totalInStudioClassesAttended")
    total_otlive_classes_attended: int = Field(..., alias="totalOtliveClassesAttended")
