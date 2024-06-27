from operator import attrgetter
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class OtfBaseModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    def __getitem__(self, key: str) -> Any:
        if key in self.model_fields:
            return getattr(self, key)

        if hasattr(self, key):
            return getattr(self, key)

        return attrgetter(key)(self)

    def get(self, key: str) -> Any:
        return self[key]
