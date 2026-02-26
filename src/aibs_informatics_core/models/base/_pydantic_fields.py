from __future__ import annotations

import datetime
import logging
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, PlainSerializer

from aibs_informatics_core.utils.functions import filter_kwargs
from aibs_informatics_core.utils.time import from_isoformat_8601


def _parse_isoish_dt(v: str | int | float | datetime.datetime) -> datetime.datetime:
    """Handle `2025-04-30T07:00:00.0` and plain `datetime` values."""
    # Convert epoch‑milliseconds first
    if isinstance(v, (int, float)):
        return datetime.datetime.fromtimestamp(v / 1_000, datetime.timezone.utc)
    # Handle ISO 8601 date‑time strings

    # Clean up iso‑format strings that may include a fractional component like ".0"
    if isinstance(v, str):
        return from_isoformat_8601(v)  # This will raise ValueError if the format is incorrect

    # Already a datetime instance → return unchanged
    return v


def _parse_date(v: str | datetime.date) -> datetime.date:
    """Handle date strings and plain `datetime.date` values."""
    if isinstance(v, str):
        return datetime.date.fromisoformat(v)
    return v


# --------------------------------------------------------------
#                     Pydantic Fields
# --------------------------------------------------------------

IsoDateTime = Annotated[
    datetime.datetime,
    BeforeValidator(_parse_isoish_dt),
    # ↓ this runs when .model_dump_json() or .model_dump(mode="json") is called
    PlainSerializer(
        lambda v: v.isoformat(),  # or v.isoformat(timespec="seconds") for no µs
        return_type=str,
        when_used="json",  # only affects JSON/dict output, not Python copy
    ),
]
IsoDate = Annotated[
    datetime.date,
    BeforeValidator(_parse_date),
    PlainSerializer(
        lambda v: v.isoformat(),  # or v.isoformat(timespec="seconds") for no µs
        return_type=str,
        when_used="json",  # only affects JSON/dict output, not Python copy
    ),
]


# --------------------------------------------------------------
#           Pydantic Marshmallow Compatibility Fields
# --------------------------------------------------------------


import marshmallow as mm  # noqa: E402


class PydanticField(mm.fields.Field):
    """Marshmallow field that uses a Pydantic model for validation and (de)serialization"""

    default_error_messages = {
        "invalid_type": "Expected {expected_type}, got {input_type}: {input!r}. {error}",
    }

    def __init__(self, pydantic_model_cls: type[BaseModel], *args, **kwargs):
        self.pydantic_model_cls = pydantic_model_cls
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        from aibs_informatics_core.models.base._pydantic_model import PydanticBaseModel

        if value is None:
            return None
        elif isinstance(value, self.pydantic_model_cls):
            if "partial" in kwargs:
                # Remove 'partial' if present, as Pydantic doesn't use it
                partial = kwargs.pop("partial")
                if partial:
                    logging.warning(
                        "Received 'partial=True' in Marshmallow deserialization, but Pydantic "
                        "does not support partial validation. Ignoring 'partial' flag."
                    )
            if isinstance(value, PydanticBaseModel):
                return value.to_dict(**kwargs)
            filtered_kwargs = filter_kwargs(value.model_dump, kwargs)
            filtered_kwargs["mode"] = "json"  # Ensure JSON serialization mode for nested models
            return value.model_dump(**filtered_kwargs)
        else:
            raise self.make_error(
                key="invalid_type",
                input=value,
                input_type=type(value),
                expected_type=self.pydantic_model_cls.__name__,
                error="",
            )

    def _deserialize(self, value, attr, data, **kwargs):
        from aibs_informatics_core.models.base._pydantic_model import PydanticBaseModel

        if value is None:
            return None
        elif isinstance(value, self.pydantic_model_cls):
            return value
        else:
            try:
                if "partial" in kwargs:
                    # Remove 'partial' if present, as Pydantic doesn't use it
                    partial = kwargs.pop("partial")
                    if partial:
                        logging.warning(
                            "Received 'partial=True' in Marshmallow deserialization, but Pydantic "
                            "does not support partial validation. Ignoring 'partial' flag."
                        )
                if issubclass(self.pydantic_model_cls, PydanticBaseModel):
                    return self.pydantic_model_cls.from_dict(value)
                return self.pydantic_model_cls.model_validate(value)
            except Exception as e:
                raise self.make_error(
                    key="invalid_type",
                    input=value,
                    input_type=type(value),
                    expected_type=self.pydantic_model_cls.__name__,
                    error=e,
                ) from e
