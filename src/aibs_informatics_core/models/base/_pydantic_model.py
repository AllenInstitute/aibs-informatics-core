from __future__ import annotations

import json
import sys
from typing import ClassVar

from pydantic import AliasGenerator, ConfigDict
from pydantic import BaseModel as _PydanticBaseModel
from pydantic.alias_generators import to_camel

from aibs_informatics_core.models.base._base_model import ModelBase
from aibs_informatics_core.models.base._pydantic_fields import PydanticField
from aibs_informatics_core.utils.json import JSONObject

if sys.version_info < (3, 11):
    from typing_extensions import Self  # type: ignore[import-untyped]
else:
    from typing import Self


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
        return cls.model_validate(data, **kwargs)

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

    @classmethod
    def as_mm_field(cls, **kwargs) -> PydanticField:
        """Helper method to create a Marshmallow field for this Pydantic model"""
        return PydanticField(cls, **kwargs)
