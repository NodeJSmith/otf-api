import inspect
import typing
from typing import ClassVar, TypeVar

from box import Box
from pydantic import BaseModel, ConfigDict

if typing.TYPE_CHECKING:
    from pydantic.main import IncEx

T = TypeVar("T", bound="OtfItemBase")


class BetterDumperMixin:
    """A better dumper for Pydantic models that includes properties in the dumped data. Must be mixed
    into a Pydantic model, as it overrides the `model_dump` method.

    Includes support for nested models, and has an option to not include properties when dumping.
    """

    def get_properties(self) -> list[str]:
        """Get the properties of the model."""
        cls = type(self)

        properties: list[str] = []
        methods = inspect.getmembers(self, lambda f: not (inspect.isroutine(f)))
        for prop_name, _ in methods:
            if hasattr(cls, prop_name) and isinstance(getattr(cls, prop_name), property):
                properties.append(prop_name)

        return properties

    @typing.overload
    def model_dump(
        self,
        *,
        mode: typing.Literal["json", "python"] | str = "python",
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        include_properties: bool = True,
    ) -> Box[str, typing.Any]: ...

    @typing.overload
    def model_dump(
        self,
        *,
        mode: typing.Literal["json", "python"] | str = "python",
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        include_properties: bool = False,
    ) -> dict[str, typing.Any]: ...

    def model_dump(
        self,
        *,
        mode: typing.Literal["json", "python"] | str = "python",
        include: "IncEx" = None,
        exclude: "IncEx" = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
        include_properties: bool = True,
    ) -> dict[str, typing.Any] | Box[str, typing.Any]:
        """Usage docs: https://docs.pydantic.dev/2.4/concepts/serialization/#modelmodel_dump

        Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

        Args:
            mode: The mode in which `to_python` should run.
                If mode is 'json', the dictionary will only contain JSON serializable types.
                If mode is 'python', the dictionary may contain any Python objects.
            include: A list of fields to include in the output.
            exclude: A list of fields to exclude from the output.
            by_alias: Whether to use the field's alias in the dictionary key if defined.
            exclude_unset: Whether to exclude fields that are unset or None from the output.
            exclude_defaults: Whether to exclude fields that are set to their default value from the output.
            exclude_none: Whether to exclude fields that have a value of `None` from the output.
            round_trip: Whether to enable serialization and deserialization round-trip support.
            warnings: Whether to log warnings when invalid fields are encountered.
            include_properties: Whether to include properties in the dumped data.

        Returns:
            A dictionary representation of the model. Will be a `Box` if `include_properties` is `True`, otherwise a
            regular dictionary.

        """
        dumped_data = typing.cast(BaseModel, super()).model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

        if not include_properties:
            return dumped_data

        properties = self.get_properties()

        # set properties to their values
        for prop_name in properties:
            dumped_data[prop_name] = getattr(self, prop_name)

        # if the property is a Pydantic model, dump it as well
        for k, v in dumped_data.items():
            if issubclass(type(getattr(self, k)), BaseModel):
                dumped_data[k] = getattr(self, k).model_dump()
            elif hasattr(v, "model_dump"):
                dumped_data[k] = v.model_dump()

        return Box(dumped_data)


class OtfItemBase(BetterDumperMixin, BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class OtfListBase(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    collection_field: ClassVar[str] = "data"

    @property
    def collection(self) -> list[OtfItemBase]:
        return getattr(self, self.collection_field)

    def to_json(self, **kwargs) -> str:
        kwargs.setdefault("indent", 4)
        kwargs.setdefault("exclude_none", True)

        return self.model_dump_json(**kwargs)
