import json
import sys
from typing import ClassVar

from aibs_informatics_core.models.base.model import ModelBase
from aibs_informatics_core.utils.json import JSONObject

if sys.version_info < (3, 11):
    from typing_extensions import Self  # type: ignore[import-untyped]
else:
    from typing import Self

try:
    from pydantic import AliasGenerator, BaseModel as _PydanticBaseModel, ConfigDict
    from pydantic.alias_generators import to_camel

except ModuleNotFoundError:  # pragma: no cover
    import types

    class _MissingPydantic(types.ModuleType):
        """Stub that raises a helpful error when any attribute is accessed."""

        __all__ = ()  # type: ignore

        def __getattr__(self, item):
            raise ImportError(
                "Optional dependency 'pydantic' is required for "
                "`aibs_informatics_core.models.base.PydanticBaseModel`. "
                "Install it with: pip install 'aibs-informatics-core[pydantic]'"
            )

    # Ensure subsequent `import pydantic` resolves to the stub so recursive
    # import attempts don’t continually re‑raise a generic ModuleNotFoundError.
    sys.modules.setdefault("pydantic", _MissingPydantic("pydantic"))

else:
    # --------------------------------------------------------------
    #                     PydanticModel
    # --------------------------------------------------------------

    class PydanticBaseModel(_PydanticBaseModel, ModelBase):
        """Base class for Pydantic models that can be serialized to/from JSON"""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            populate_by_name=True,
            extra="ignore",
            alias_generator=AliasGenerator(
                # Use custom alias generators for validation and serialization
                # to ensure camelCase to snake_case conversion
                # and vice versa, depending on the context.
                validation_alias=to_camel,
                serialization_alias=to_camel,
            ),
        )

        @classmethod
        def from_dict(cls, data: JSONObject, **kwargs) -> Self:
            return cls.model_validate(
                data,
                **kwargs,
            )

        def to_dict(self, **kwargs) -> JSONObject:
            # Ensure None values are excluded by default to mirror DataClassJsonMixin settings
            exclude_none = kwargs.pop("exclude_none", True)
            mode = kwargs.pop("mode", "json")
            return self.model_dump(
                mode=mode,  # Use JSON serialization mode
                exclude_none=exclude_none,  # Exclude None values by default
                **kwargs,
            )

        @classmethod
        def from_json(cls, data: str, **kwargs) -> Self:
            return cls.from_dict(json.loads(data), **kwargs)
