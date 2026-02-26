from __future__ import annotations

import json
import sys
from functools import cache
from typing import Any, ClassVar, Optional, get_args, get_origin

from aibs_informatics_core.models.base.model import ModelBase
from aibs_informatics_core.utils.json import JSONObject

if sys.version_info < (3, 11):
    from typing_extensions import Self  # type: ignore[import-untyped]
else:
    from typing import Self

try:
    from pydantic import AliasGenerator, ConfigDict, TypeAdapter, ValidationError, create_model
    from pydantic import BaseModel as _PydanticBaseModel
    from pydantic.alias_generators import to_camel

except ModuleNotFoundError:  # pragma: no cover
    import types

    class _MissingPydantic(types.ModuleType):
        __all__ = ()  # type: ignore

        def __getattr__(self, item):
            raise ImportError(
                "Dependency 'pydantic' is required for "
                "`aibs_informatics_core.models.base.PydanticBaseModel`."
            )

    sys.modules.setdefault("pydantic", _MissingPydantic("pydantic"))

else:

    def _is_optional(annotation: Any) -> bool:
        origin = get_origin(annotation)
        if origin is None:
            return False
        return type(None) in get_args(annotation)

    class PydanticBaseModel(_PydanticBaseModel, ModelBase):
        """Canonical project model base built on pydantic."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            populate_by_name=True,
            extra="ignore",
            arbitrary_types_allowed=True,
            validate_assignment=True,
            alias_generator=AliasGenerator(
                validation_alias=to_camel,
                serialization_alias=to_camel,
            ),
        )

        def __init__(self, *args, **kwargs):
            if args:
                field_names = list(type(self).model_fields.keys())
                if len(args) > len(field_names):
                    raise TypeError(
                        f"{type(self).__name__} expected at most {len(field_names)} positional "
                        f"args but got {len(args)}"
                    )
                for i, value in enumerate(args):
                    field_name = field_names[i]
                    if field_name in kwargs:
                        raise TypeError(
                            f"{type(self).__name__} got multiple values for field "
                            f"'{field_name}'"
                        )
                    kwargs[field_name] = value
            super().__init__(**kwargs)

        @classmethod
        @cache
        def partial_model(cls) -> type["PydanticBaseModel"]:
            fields: dict[str, tuple[Any, None]] = {}
            required_fields: set[str] = set()
            for field_name, field in cls.model_fields.items():
                annotation = field.annotation
                if annotation is None:
                    annotation = Any
                optional_annotation = annotation if _is_optional(annotation) else Optional[annotation]
                fields[field_name] = (optional_annotation, None)
                if field.is_required():
                    required_fields.add(field_name)

            partial_cls = create_model(  # type: ignore[return-value]
                f"{cls.__name__}Partial",
                __base__=cls,
                __module__=cls.__module__,
                **fields,
            )
            setattr(partial_cls, "__partial_source_required_fields__", required_fields)
            setattr(partial_cls, "__partial_source_model__", cls)
            return partial_cls

        @classmethod
        def from_dict(cls, data: JSONObject, **kwargs) -> Self | list[Self]:
            many = kwargs.pop("many", False)
            partial = kwargs.pop("partial", False)

            model_cls: type[PydanticBaseModel] = cls.partial_model() if partial else cls
            if many:
                return TypeAdapter(list[model_cls]).validate_python(data, **kwargs)  # type: ignore[return-value]

            return model_cls.model_validate(data, **kwargs)  # type: ignore[return-value]

        def to_dict(self, **kwargs) -> JSONObject:
            kwargs.pop("validate", None)
            kwargs.pop("many", None)
            partial = kwargs.pop("partial", False)

            mode = kwargs.pop("mode", "json")
            by_alias = kwargs.pop("by_alias", False)
            exclude_none = kwargs.pop("exclude_none", True)
            exclude_unset = kwargs.pop("exclude_unset", partial)
            return self.model_dump(
                mode=mode,
                by_alias=by_alias,
                exclude_none=exclude_none,
                exclude_unset=exclude_unset,
                **kwargs,
            )

        @classmethod
        def from_json(cls, data: str, **kwargs) -> Self | list[Self]:
            return cls.from_dict(json.loads(data), **kwargs)

        def to_json(self, **kwargs) -> str:
            sort_keys = kwargs.pop("sort_keys", False)
            return json.dumps(self.to_dict(**kwargs), indent=4, sort_keys=sort_keys)

        @classmethod
        def validate(cls, data: JSONObject | Self, **kwargs) -> None:
            if isinstance(data, cls):
                cls.model_validate(data.model_dump(mode="python"), **kwargs)
                return
            cls.from_dict(data, **kwargs)

        @classmethod
        def is_valid(cls, data: JSONObject | Self, **kwargs) -> bool:
            try:
                cls.validate(data, **kwargs)
            except ValidationError:
                return False
            return True

        @classmethod
        def empty(cls) -> Self:
            return cls.from_dict({}, partial=True)  # type: ignore[return-value]

        def copy(self, partial: bool = False, **kwargs) -> Self:
            return type(self).from_dict(self.to_dict(partial=partial, **kwargs), partial=partial)  # type: ignore[return-value]

        def is_partial(self) -> bool:
            required_fields = getattr(type(self), "__partial_source_required_fields__", None)
            if required_fields is None:
                required_fields = {
                    name for name, field in type(self).model_fields.items() if field.is_required()
                }
            return any(name not in self.model_fields_set for name in required_fields)

        @classmethod
        def as_mm_field(cls, *args, **kwargs):
            # Legacy helper retained only for construction-time no-op compatibility
            return cls
