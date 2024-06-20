from operator import attrgetter, itemgetter
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class OtfBaseModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def get(self, key: str) -> Any:
        try:
            return attrgetter(key)(self)
        except AttributeError:
            return itemgetter(key)(self)
