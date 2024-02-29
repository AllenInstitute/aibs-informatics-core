__all__ = [
    "FieldMetadataBuilder",
    "FieldProps",
    "custom_field",
    "field_metadata",
]


from dataclasses import MISSING, Field, dataclass
from dataclasses import field as dataclasses_field
from enum import Enum
from typing import Any, Callable, Dict, Mapping, Optional, Type, TypeVar, cast, overload

import marshmallow as mm
from dataclasses_json import config, global_config
from typing_inspect import is_optional_type as _is_optional_type

from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.tools.dicttools import remove_null_values

T = TypeVar("T")
S = TypeVar("S", bound=str)
E = TypeVar("E", bound=Enum)

FieldMetadata = Dict[str, dict]

EncoderType = Callable[[T], JSON]
DecoderType = Callable[[JSON], T]


# --------------------------------------------------------------
#                     Field Metadata Builder
# --------------------------------------------------------------


@dataclass
class FieldMetadataBuilder:
    mm_field: Optional[mm.fields.Field] = None
    encoder: Optional[EncoderType] = None
    decoder: Optional[DecoderType] = None

    def build(self, required: Optional[bool] = None, **kwargs) -> FieldMetadata:
        mm_field = self.mm_field
        encoder = self.encoder
        decoder = self.decoder

        # set allow_none to !required IF required is explicitly specified (True/False).
        allow_none = not required if required is not None else required

        if mm_field is None:
            mm_field_cls = self.create_mm_field_class(encoder=encoder, decoder=decoder)
            mm_field_kwargs: dict[str, Any] = {}
            if required is not None:
                mm_field_kwargs["required"] = required
            mm_field = mm_field_cls(**mm_field_kwargs)
            if allow_none is not None:
                mm_field.allow_none = allow_none

        else:
            if required is not None:
                mm_field.required = required
                if allow_none is not None:
                    mm_field.allow_none = allow_none
            if encoder is None:
                encoder = self.create_encoder_from_mm_field(mm_field)
            if decoder is None:
                decoder = self.create_decoder_from_mm_field(mm_field)

        return config(encoder=encoder, decoder=decoder, mm_field=mm_field, **kwargs)

    def add_to_global_config(
        self,
        clazz: Type[Any],
        required: Optional[bool] = None,
        skip_mm_field: bool = False,
        skip_encoder: bool = False,
        skip_decoder: bool = False,
        **kwargs,
    ):
        dataclass_json_config = self.build(required=required, **kwargs)["dataclasses_json"]

        if "mm_field" in dataclass_json_config and not skip_mm_field:
            global_config.mm_fields[clazz] = dataclass_json_config["mm_field"]
        if "encoder" in dataclass_json_config and not skip_encoder:
            global_config.encoders[clazz] = dataclass_json_config["encoder"]
        if "decoder" in dataclass_json_config and not skip_decoder:
            global_config.decoders[clazz] = dataclass_json_config["decoder"]

    @classmethod
    def create_mm_field_class(
        cls, encoder: Optional[EncoderType], decoder: Optional[DecoderType]
    ) -> Type[mm.fields.Field]:
        """Creates a Marshmallow Field with optional encoder/decoder overrides

        Args:
            encoder (Optional[EncoderType]): Optional encoder function
            decoder (Optional[DecoderType]): Optional decoder function

        Returns:
            Type[mm.fields.Field]: _description_
        """

        class CustomField(mm.fields.Field):
            def _serialize(self, value, attr, obj, **kwargs):
                if encoder:
                    return encoder(value)
                return super()._serialize(value, attr, obj, **kwargs)

            def _deserialize(self, value, attr, data, **kwargs):
                if decoder:
                    return decoder(value)
                return super()._deserialize(value, attr, data, **kwargs)

        return CustomField

    @classmethod
    def create_encoder_from_mm_field(cls, mm_field: mm.fields.Field) -> EncoderType:
        def mm_field_encoder(value):
            return mm_field.serialize("", value, lambda _1, _2, _3: value)

        return cast(EncoderType, mm_field_encoder)

    @classmethod
    def create_decoder_from_mm_field(cls, mm_field: mm.fields.Field) -> DecoderType:
        def mm_field_decoder(value):
            return mm_field.deserialize(value)

        return cast(DecoderType, mm_field_decoder)


def field_metadata(
    mm_field: Optional[mm.fields.Field] = None,
    encoder: Optional[EncoderType] = None,
    decoder: Optional[DecoderType] = None,
    required: Optional[bool] = None,
    **kwargs,
) -> FieldMetadata:
    return FieldMetadataBuilder(mm_field=mm_field, encoder=encoder, decoder=decoder).build(
        required=required, **kwargs
    )


# --------------------------------------------------------------
#               Dataclass Utility Functions
# --------------------------------------------------------------


@dataclass
class FieldProps:
    field: Field

    def requires_init(self) -> bool:
        return not self.has_default()

    def is_optional_type(self) -> bool:
        return _is_optional_type(self.field.type)

    def has_default(self) -> bool:
        return not (self.field.default_factory is MISSING and self.field.default is MISSING)  # type: ignore[misc]


@overload
def custom_field(
    *,
    default: Optional[T],
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    mm_field: Optional[mm.fields.Field] = None,
    encoder: Optional[EncoderType] = None,
    decoder: Optional[DecoderType] = None,
) -> T:
    ...  # pragma: no cover


@overload
def custom_field(
    *,
    default_factory: Callable[[], T],
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    mm_field: Optional[mm.fields.Field] = None,
    encoder: Optional[EncoderType] = None,
    decoder: Optional[DecoderType] = None,
) -> T:
    ...  # pragma: no cover


@overload
def custom_field(
    *,
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    mm_field: Optional[mm.fields.Field] = None,
    encoder: Optional[EncoderType] = None,
    decoder: Optional[DecoderType] = None,
) -> Any:
    ...  # pragma: no cover


def custom_field(
    *,
    # Below values mirror those found in `dataclasses.field`
    default: Any = MISSING,
    default_factory: Callable[[], Any] = MISSING,  # type: ignore
    init: bool = True,
    repr: bool = True,
    hash: Optional[bool] = None,
    compare: bool = True,
    metadata: Optional[Mapping[Any, Any]] = None,
    # Following are custom
    mm_field: Optional[mm.fields.Field] = None,
    encoder: Optional[EncoderType] = None,
    decoder: Optional[DecoderType] = None,
) -> Any:
    """Convenience function for generating a Dataclass Field WITH Encoders/Decoders/ MM Fields

    Args:
        mm_field (mm.fields.Field, optional): _description_. Defaults to None.
        encoder (EncoderType, optional): _description_. Defaults to None.
        decoder (DecoderType, optional): . Defaults to None.
        default (Any, optional): Default value if not provided. Defaults to MISSING.
        default_factory (Callable[[], Any], optional): _description_. Defaults to MISSING.
        repr (bool, optional): _description_. Defaults to True.
        hash (Optional[bool], optional): _description_. Defaults to None.
        compare (bool, optional): _description_. Defaults to True.
        metadata (Optional[Mapping[Any, Any]], optional): _description_. Defaults to None.

    Returns:
        Field: _description_
    """
    required = init and not (default != MISSING or default_factory != MISSING)
    metadata = field_metadata(
        mm_field=mm_field,
        encoder=encoder,
        decoder=decoder,
        required=required,
        metadata=metadata,
    )
    if default != MISSING:
        return dataclasses_field(
            default=default,
            init=init,
            compare=compare,
            hash=hash,
            repr=repr,
            metadata=metadata,
        )
    elif default_factory != MISSING:
        return dataclasses_field(
            default_factory=default_factory,
            init=init,
            compare=compare,
            hash=hash,
            repr=repr,
            metadata=metadata,
        )
    else:
        return dataclasses_field(
            init=init,
            compare=compare,
            hash=hash,
            repr=repr,
            metadata=metadata,
        )


# to make it synonymous with dataclasses.field
field = custom_field
