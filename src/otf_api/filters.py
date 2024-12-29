from datetime import date, time

from pydantic import BaseModel, field_validator

from otf_api.models import ClassType, DoW, OtfClass


class ClassFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    class_type: list[ClassType] | None = None
    day_of_week: list[DoW] | None = None
    start_time: list[time] | None = None

    @field_validator("class_type", "day_of_week", "start_time", mode="before")
    @classmethod
    def single_item_to_list(cls, v):
        if v and not isinstance(v, list):
            return [v]
        return v

    @field_validator("day_of_week", mode="before")
    @classmethod
    def day_of_week_str_to_enum(cls, v):
        if v and isinstance(v, str):
            return [DoW(v.title())]

        if v and isinstance(v, list) and not all(isinstance(i, DoW) for i in v):
            return [DoW(i.title()) for i in v]

        return v

    @field_validator("class_type", mode="before")
    @classmethod
    def class_type_str_to_enum(cls, v):
        if v and isinstance(v, str):
            return [ClassType.get_case_insensitive(v)]

        if v and isinstance(v, list) and not all(isinstance(i, ClassType) for i in v):
            return [ClassType.get_case_insensitive(i) for i in v]

        return v

    def filter_classes(self, classes: list[OtfClass]) -> list[OtfClass]:
        if self.start_date:
            classes = [c for c in classes if c.starts_at_local.date() >= self.start_date]
        if self.end_date:
            classes = [c for c in classes if c.starts_at_local.date() <= self.end_date]
        if self.class_type:
            classes = [c for c in classes if c.class_type in self.class_type]
        if self.day_of_week:
            classes = [c for c in classes if c.day_of_week in self.day_of_week]
        if self.start_time:
            classes = [c for c in classes if c.starts_at_local.time() in self.start_time]
        return classes
