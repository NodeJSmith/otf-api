from pydantic import BaseModel, ConfigDict


class OtfBaseModel(BaseModel):
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
