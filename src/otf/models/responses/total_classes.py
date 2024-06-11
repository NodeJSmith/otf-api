from pydantic import BaseModel, Field


class TotalClasses(BaseModel):
    total_in_studio_classes_attended: int = Field(..., alias="totalInStudioClassesAttended")
    total_otlive_classes_attended: int = Field(..., alias="totalOtliveClassesAttended")
