from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class OtfItemBase(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="allow")


class OtfListBase(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    collection_field: ClassVar[str] = "data"

    @property
    def collection(self) -> list[OtfItemBase]:
        return getattr(self, self.collection_field)

    def to_json(self, **kwargs) -> str:
        kwargs.setdefault("indent", 4)
        kwargs.setdefault("exclude_none", True)

        return self.model_dump_json(**kwargs)
