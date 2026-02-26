__all__ = [
    "FieldMetadataBuilder",
    "FieldProps",
    "custom_field",
    "field_metadata",
]

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeVar, overload

from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

T = TypeVar("T")

FieldMetadata = dict[str, Any]

EncoderType = Callable[[T], Any]
DecoderType = Callable[[Any], T]


@dataclass
class FieldMetadataBuilder:
    mm_field: Any | None = None
    encoder: EncoderType | None = None
    decoder: DecoderType | None = None

    def build(self, required: bool | None = None, **kwargs) -> FieldMetadata:
        metadata = {
            "mm_field": self.mm_field,
            "encoder": self.encoder,
            "decoder": self.decoder,
            "required": required,
        }
        metadata.update(kwargs)
        return metadata

    def add_to_global_config(self, *args, **kwargs):
        return None


def field_metadata(
    mm_field: Any | None = None,
    encoder: EncoderType | None = None,
    decoder: DecoderType | None = None,
    required: bool | None = None,
    **kwargs,
) -> FieldMetadata:
    return FieldMetadataBuilder(mm_field=mm_field, encoder=encoder, decoder=decoder).build(
        required=required, **kwargs
    )


@dataclass
class FieldProps:
    field: Any

    def requires_init(self) -> bool:
        if isinstance(self.field, FieldInfo):
            return self.field.is_required()
        is_required = getattr(self.field, "is_required", None)
        if callable(is_required):
            return bool(is_required())
        return False

    def is_optional_type(self) -> bool:
        annotation = getattr(self.field, "annotation", None) or getattr(self.field, "type", None)
        if annotation is None:
            return True
        return getattr(annotation, "__origin__", None) is None and annotation is Any

    def has_default(self) -> bool:
        return not self.requires_init()


@overload
def custom_field(
    *,
    default: T | None,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: Mapping[Any, Any] | None = None,
    mm_field: Any | None = None,
    encoder: EncoderType | None = None,
    decoder: DecoderType | None = None,
) -> T: ...  # pragma: no cover


@overload
def custom_field(
    *,
    default_factory: Callable[[], T],
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: Mapping[Any, Any] | None = None,
    mm_field: Any | None = None,
    encoder: EncoderType | None = None,
    decoder: DecoderType | None = None,
) -> T: ...  # pragma: no cover


@overload
def custom_field(
    *,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: Mapping[Any, Any] | None = None,
    mm_field: Any | None = None,
    encoder: EncoderType | None = None,
    decoder: DecoderType | None = None,
) -> Any: ...  # pragma: no cover


def custom_field(
    *,
    default: Any = PydanticUndefined,
    default_factory: Callable[[], Any] | Any = PydanticUndefined,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: Mapping[Any, Any] | None = None,
    mm_field: Any | None = None,
    encoder: EncoderType | None = None,
    decoder: DecoderType | None = None,
) -> Any:
    json_schema_extra: dict[str, Any] = {}
    if metadata is not None:
        json_schema_extra["metadata"] = dict(metadata)
    if mm_field is not None:
        json_schema_extra["mm_field"] = mm_field
    if encoder is not None:
        json_schema_extra["encoder"] = encoder
    if decoder is not None:
        json_schema_extra["decoder"] = decoder
    if hash is not None:
        json_schema_extra["hash"] = hash
    if compare is not None:
        json_schema_extra["compare"] = compare

    kwargs: dict[str, Any] = {
        "repr": repr,
    }
    if json_schema_extra:
        kwargs["json_schema_extra"] = json_schema_extra

    if default_factory is not PydanticUndefined:
        return Field(default_factory=default_factory, **kwargs)
    if default is not PydanticUndefined:
        return Field(default=default, **kwargs)
    if init:
        return Field(default=PydanticUndefined, **kwargs)
    return Field(default=None, exclude=True, **kwargs)


field = custom_field
