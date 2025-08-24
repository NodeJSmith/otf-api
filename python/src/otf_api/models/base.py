from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class OtfItemBase(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True, 
        extra="ignore",
        # Use Python field names in schema generation (not validation_alias)
        by_alias=False
    )
