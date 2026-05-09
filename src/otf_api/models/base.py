from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class OtfItemBase(BaseModel):
    """Base model for all OTF API response objects, configured to ignore unknown fields."""

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
