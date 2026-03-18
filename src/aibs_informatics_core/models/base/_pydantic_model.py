from __future__ import annotations

from typing import ClassVar, Self

from pydantic import AliasGenerator, ConfigDict
from pydantic import BaseModel as _PydanticBaseModel
from pydantic.alias_generators import to_camel
from pydantic_core import ValidationError as PydanticValidationError

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.base._base_model import ModelBase
from aibs_informatics_core.utils.functions import filter_kwargs
from aibs_informatics_core.utils.json import JSONObject

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
        """Create an instance from a dictionary using Pydantic validation.

        Args:
            data: Dictionary representation of the model.
            **kwargs: Additional keyword arguments passed to ``model_validate``.

        Returns:
            A validated instance of the model.

        Raises:
            ValidationError: If the data fails Pydantic validation.
        """
        try:
            return cls.model_validate(data, **filter_kwargs(cls.model_validate, kwargs))
        except PydanticValidationError as e:
            # TODO: Need to figure out whether to use Pydantic's ValidationError or our own,
            #       and how to best preserve error details
            raise ValidationError(str(e)) from e

    def to_dict(self, **kwargs) -> JSONObject:
        """Serialize the model to a dictionary using Pydantic serialization.

        By default, None values are excluded and JSON-compatible serialization
        mode is used.

        Args:
            **kwargs: Additional keyword arguments passed to ``model_dump``.
                Supports ``exclude_none`` (default: True) and ``mode``
                (default: "json").

        Returns:
            Dictionary representation of the model.

        Raises:
            ValidationError: If serialization fails Pydantic validation.
        """
        # Ensure None values are excluded by default to mirror DataClassJsonMixin settings
        exclude_none = kwargs.pop("exclude_none", True)
        mode = kwargs.pop("mode", "json")
        try:
            return self.model_dump(
                mode=mode,  # Use JSON serialization mode
                exclude_none=exclude_none,  # Exclude None values by default
                **filter_kwargs(self.model_dump, kwargs),
            )
        except PydanticValidationError as e:
            raise ValidationError(str(e)) from e
