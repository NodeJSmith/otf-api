from pydantic import BaseModel, Field


class MaxHr(BaseModel):
    type: str
    value: int


class DnaMaxHr(BaseModel):
    member_uuid: str = Field(..., alias="memberUuid")
    max_hr: MaxHr = Field(..., alias="maxHr")
