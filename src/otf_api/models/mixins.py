from datetime import datetime

from humanize import precisedelta

from otf_api.models.enums import ClassType


class OtfClassTimeMixin:
    starts_at_local: datetime
    ends_at_local: datetime
    name: str

    @property
    def day_of_week(self) -> str:
        return self.starts_at_local.strftime("%A")

    @property
    def date(self) -> str:
        return self.starts_at_local.strftime("%Y-%m-%d")

    @property
    def time(self) -> str:
        """Returns time in 12 hour clock format, with no leading 0"""
        val = self.starts_at_local.strftime("%I:%M %p")
        if val[0] == "0":
            val = " " + val[1:]

        return val

    @property
    def duration(self) -> str:
        duration = self.ends_at_local - self.starts_at_local
        human_val: str = precisedelta(duration, minimum_unit="minutes")
        if human_val == "1 hour and 30 minutes":
            return "90 minutes"
        return human_val

    @property
    def class_type(self) -> ClassType:
        for class_type in ClassType:
            if class_type.value in self.name:
                return class_type

        return ClassType.OTHER
