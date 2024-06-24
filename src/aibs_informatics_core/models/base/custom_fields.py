__all__ = [
    "BooleanField",
    "CustomAwareDateTime",
    "CustomStringField",
    "DictField",
    "EnumField",
    "FloatField",
    "FrozenSetField",
    "IntegerField",
    "ListField",
    "MappingField",
    "NestedField",
    "PathField",
    "RawField",
    "StringField",
    "TupleField",
    "UnionField",
    "UUIDField",
]

import datetime as dt
import uuid
from collections import defaultdict
from enum import Enum
from inspect import isfunction
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import marshmallow as mm
from marshmallow import utils as mm_utils

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.base.field_utils import FieldMetadataBuilder
from aibs_informatics_core.utils.json import JSON

T = TypeVar("T")
S = TypeVar("S", bound=str)
E = TypeVar("E", bound=Enum)

FieldMetadata = Dict[str, dict]

EncoderType = Callable[[T], JSON]
DecoderType = Callable[[JSON], T]


# --------------------------------------------------------------
#                  Custom Marshmallow Fields
# --------------------------------------------------------------


class EnumField(mm.fields.Field, Generic[E]):
    default_error_messages = {
        "invalid_value": "'{input}' is not a valid value of {obj_type}.",
        "not_enum": "'{input}' (type: {input_type}) is not an Enum type.",
    }

    def __init__(self, enum: Type[E], *args, **kwargs):
        self.enum_cls = enum
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        if value is None:
            return None
        else:
            if isinstance(value, self.enum_cls):
                return value.value
            else:
                raise self.make_error(key="not_enum", input=value, input_type=type(value))

    def _deserialize(self, value, attr, data, **kwargs) -> Optional[E]:
        if value is None:
            return None
        else:
            try:
                return self.enum_cls(value)
            except ValueError as e:
                enum_name = self.enum_cls.__name__
                raise self.make_error(key="invalid_value", input=value, obj_type=enum_name) from e


class PathField(mm.fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return str(value) if isinstance(value, Path) else value

    def _deserialize(self, value, attr, data, **kwargs):
        return Path(value)


class FrozenSetField(mm.fields.List):
    def _serialize(self, value, *args, **kwargs):
        return super()._serialize(sorted(list(value)), *args, **kwargs)

    def _deserialize(self, *args, **kwargs):
        return frozenset(super()._deserialize(*args, **kwargs))


class CustomStringField(mm.fields.String, Generic[S]):
    default_error_messages = {
        "invalid_type": "'{input}' (type: {input_type}) is not a {expected_type} type!"
    }

    def __init__(self, str_cls: Type[S], *args, strict_mode: bool = False, **kwargs):
        """Field for subclassed string types.

        Deserialized values are constructed using subclass string type.

        By default, the serialization is relaxed on what inputs can be converted to strings
        (mirroring the default mm.fields.String behavior). i.e.
        If strict_mode is enabled, however, the

        Args:
            str_cls (Type[S]): _description_
            strict_mode (bool, optional): _description_. Defaults to False.
        """
        self.str_cls = str_cls
        self.strict_mode = strict_mode
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        if value is None:
            return None
        elif not issubclass(type(value), self.str_cls):
            if not self._can_as(value):
                raise self._make_invalid_type_error(value=value)
            value = self.str_cls(value)
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs) -> Optional[S]:
        deserialized_value = super()._deserialize(value=value, attr=attr, data=data, **kwargs)
        return self.str_cls(deserialized_value) if deserialized_value is not None else None

    def _make_invalid_type_error(self, value: Any) -> mm.ValidationError:
        return self.make_error(
            key="invalid_type",
            input=value,
            input_type=type(value),
            expected_type=self.str_cls,
        )

    def _can_as(self, value) -> bool:
        if self.strict_mode and not isinstance(value, self.str_cls):
            return False
        try:
            self.str_cls(value)
        except:
            return False
        return True


class CustomAwareDateTime(mm.fields.AwareDateTime):
    """Version of marshmallow AwareDateTime field that allows an already deserialized
    (iso8601 str -> dt.datetime) AwareDateTime field to be passed through deserialization again
    (dt.datetime -> dt.datetime)

    This is necessary because the BaseModel may do a deserialization via the `load` method and
    then do another deserialization via the __setattr__ validation (which calls another
    deserialization to validate).

    Base implementation can be found here:
    https://marshmallow.readthedocs.io/en/stable/_modules/marshmallow/fields.html#AwareDateTime
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dt.datetime):
            if not mm_utils.is_aware(value):
                if self.default_timezone is None:
                    raise self.make_error(
                        "invalid_awareness",
                        awareness=self.AWARENESS,
                        obj_type=self.OBJ_TYPE,
                    )
                return value.replace(tzinfo=self.default_timezone)
            return value
        return super()._deserialize(value, attr, data, **kwargs)


TypeOrTupleOfTypes = Union[Type[Any], Tuple[Type[Any], ...]]
UnionFieldsType = Tuple[
    Union[TypeOrTupleOfTypes, Callable[[], TypeOrTupleOfTypes]],
    Union[mm.fields.Field, Callable[[], mm.fields.Field]],
]


class UnionField(mm.fields.Field):
    default_error_messages = {
        "invalid_type": "'{input}' (type: {input_type}) is not one of {expected_types} type!",
        "unexpected_error": "Unexpected error occurred: {error}",
        "unsupported_serialize": (
            "'{input}' (type: {input_type}) was not serializable "
            "by any of the {expected_types} fields!: {error_messages}"
        ),
        "unsupported_deserialize": (
            "'{input}' (type: {input_type}) was not handled "
            "by any of the {expected_types} fields!: {error_messages}"
        ),
    }

    def __init__(self, union_fields: Sequence[UnionFieldsType], *args, **kwargs):
        self._raw_union_fields: Sequence[UnionFieldsType] = union_fields
        self._union_fields: Dict[Type[Any], List[mm.fields.Field]] = None  # type: ignore
        super().__init__(*args, **kwargs)

    @property
    def union_fields(self) -> Dict[Type[Any], List[mm.fields.Field]]:
        if self._union_fields is None:
            self._union_fields = defaultdict(list)
            for union_type, union_field in self._raw_union_fields:
                if isfunction(union_type):
                    union_type = cast(Callable[[], TypeOrTupleOfTypes], union_type)()
                union_types = union_type if isinstance(union_type, tuple) else (union_type,)
                if isfunction(union_field):
                    union_field = union_field()

                for union_type in union_types:
                    self._union_fields[cast(Type[Any], union_type)].append(
                        cast(mm.fields.Field, union_field)
                    )
        return self._union_fields

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        if value is None:
            return None
        input_type = type(value)
        errors: Dict[Type[Any], List[mm.ValidationError]] = defaultdict(list)
        for class_type, class_fields in self.union_fields.items():
            if issubclass(input_type, class_type):
                for class_field in class_fields:
                    try:
                        return class_field._serialize(value, attr=attr, obj=obj, **kwargs)
                    except mm.ValidationError as e:
                        errors[class_type].append(e)
                    except Exception as e:
                        print(e)
                        errors[class_type].append(self.make_error(key="unexpected_error", error=e))
        else:
            if len(errors):
                raise self.make_error(
                    key="unsupported_serialize",
                    input=value,
                    input_type=input_type,
                    expected_types=list(self.union_fields.keys()),
                    error_messages={
                        _.__name__: [e.normalized_messages() for e in e_list]
                        for _, e_list in errors.items()
                    },
                )

            raise self.make_error(
                key="invalid_type",
                input=value,
                input_type=input_type,
                expected_types=list(self.union_fields.keys()),
            )

    def _deserialize(self, value, attr, data, **kwargs) -> Optional[E]:
        if value is None:
            return None
        else:
            errors: Dict[Type[Any], List[mm.ValidationError]] = defaultdict(list)
            for class_type, class_fields in self.union_fields.items():
                for class_field in class_fields:
                    try:
                        return class_field._deserialize(
                            value=value, attr=attr, data=data, **kwargs
                        )
                    except (mm.ValidationError, ValidationError) as e:
                        if not isinstance(e, mm.ValidationError):
                            e = self.make_error(key="unexpected_error", error=e)
                        errors[class_type].append(e)
            else:
                raise self.make_error(
                    key="unsupported_deserialize",
                    input=value,
                    input_type=type(value),
                    expected_types=list(self.union_fields.values()),
                    error_messages={
                        _.__name__: [e.normalized_messages() for e in e_list]
                        for _, e_list in errors.items()
                    },
                )


BooleanField = mm.fields.Boolean
DictField = mm.fields.Dict
FloatField = mm.fields.Float
IntegerField = mm.fields.Integer
MappingField = mm.fields.Mapping
NestedField = mm.fields.Nested
ListField = mm.fields.List
RawField = mm.fields.Raw
StringField = mm.fields.String
TupleField = mm.fields.Tuple
UUIDField = mm.fields.UUID


# --------------------------------------------------------------
#                   Global Configurations
# --------------------------------------------------------------


FieldMetadataBuilder(mm_field=CustomAwareDateTime("iso8601")).add_to_global_config(
    dt.datetime, required=False, skip_mm_field=True
)

FieldMetadataBuilder(mm_field=UUIDField()).add_to_global_config(
    uuid.UUID, required=False, skip_mm_field=True
)
