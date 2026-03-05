__all__ = [
    "BaseSchema",
    "DataClassModel",
    "MISSING",
    "NONE",
    "SchemaModel",
    "post_dump",
    "pre_dump",
    "pre_load",
    "validates_schema",
]

import inspect
import json
from dataclasses import MISSING as dataclass_MISSING
from dataclasses import Field, dataclass, fields
from functools import wraps
from types import MethodType
from typing import (
    Any,
    ClassVar,
    Protocol,
    Self,
    TypeVar,
    cast,
    get_type_hints,
)

import marshmallow as mm
from dataclasses_json import DataClassJsonMixin, Undefined, config
from dataclasses_json.core import _ExtendedEncoder
from marshmallow import post_dump, pre_dump, pre_load, validates_schema
from marshmallow.decorators import POST_LOAD
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from aibs_informatics_core.models.base._base_model import ModelBase
from aibs_informatics_core.models.base.custom_fields import NestedField
from aibs_informatics_core.models.base.field_utils import FieldProps
from aibs_informatics_core.utils.decorators import cache
from aibs_informatics_core.utils.json import JSONObject
from aibs_informatics_core.utils.tools.dicttools import remove_matching_values

T = TypeVar("T")


DEFAULT_PARTIAL = False
DEFAULT_VALIDATE = True

DCM = TypeVar("DCM", bound="DataClassModel")
SM = TypeVar("SM", bound="SchemaModel")


# --------------------------------------------------------------
#                        DataClassModel
# --------------------------------------------------------------


class DataClassModel(DataClassJsonMixin, ModelBase):
    dataclass_json_config: ClassVar[dict] = config(  # type: ignore[misc]
        undefined=Undefined.EXCLUDE,  # default behavior for handling undefined fields
        exclude=lambda f: f is None,  # excludes values if None by default
    )["dataclasses_json"]

    @classmethod
    def from_dict(  # type: ignore[override]
        cls, data: JSONObject, partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> Self:
        return super().from_dict(data, infer_missing=partial)

    def to_dict(self, partial: bool = DEFAULT_PARTIAL, **kwargs) -> JSONObject:  # type: ignore[override]
        return super().to_dict(encode_json=kwargs.get("encode_json", True))

    @classmethod
    def from_json(cls, data: str, **kwargs) -> Self:  # type: ignore[override]
        return cls.from_dict(json.loads(data), **kwargs)

    def to_json(self, **kwargs) -> str:
        json_encoder_cls: type[json.JSONEncoder] = kwargs.pop("json_encoder", _ExtendedEncoder)
        return json.dumps(self.to_dict(**kwargs), indent=4, cls=json_encoder_cls)

    @classmethod
    @cache
    def get_model_fields(cls) -> tuple[Field, ...]:
        resolved: dict[str, type] | None = None
        class_fields = fields(cls)  # type: ignore[arg-type]
        for f in class_fields:
            # There is a bug with https://peps.python.org/pep-0563/
            # (postponed evaluation of annotations) where the type of the field is a string.
            # This is a workaround for that issue.
            # https://stackoverflow.com/a/55938344/4544508
            if isinstance(f.type, str):
                # This avoids running `get_type_hints` unnecessarily
                if resolved is None:
                    resolved = get_type_hints(cls)
                f.type = resolved[f.name]

        return class_fields  # type: ignore[arg-type]

    @classmethod
    def is_missing(cls, value: Any) -> bool:
        return value is dataclass_MISSING or value is MISSING or value is ...

    @classmethod
    def __get_pydantic_core_schema__(  # noqa: C901
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        # 1. Define how to turn incoming data into an instance
        def validate(value: Any) -> Any:
            # If it's already the right object type, return it
            if isinstance(value, cls):
                return value
            # If it's a dict, use your custom from_dict
            if isinstance(value, dict):
                return cls.from_dict(value)
            # If it's a JSON string, use your custom from_json
            if isinstance(value, str):
                return cls.from_json(value)
            raise ValueError(f"Cannot convert {type(value)} to {cls.__name__}")

        # 2. Build a typed-dict schema from dataclass fields for JSON schema generation
        json_input_schema: CoreSchema = core_schema.dict_schema()
        if hasattr(source_type, "__dataclass_fields__"):
            try:
                type_hints = get_type_hints(source_type)
                td_fields: Dict[str, Any] = {}
                for f in fields(source_type):
                    if f.name.startswith("_"):
                        continue
                    field_type = type_hints.get(f.name)
                    if field_type is None:
                        continue
                    try:
                        field_schema = handler(field_type)
                    except Exception:
                        field_schema = core_schema.any_schema()
                    is_required = (
                        f.default is dataclass_MISSING and f.default_factory is dataclass_MISSING
                    )
                    td_field_kwargs: Dict[str, Any] = {}
                    if not is_required:
                        td_field_kwargs["required"] = False
                    td_fields[f.name] = core_schema.typed_dict_field(
                        schema=field_schema,
                        **td_field_kwargs,
                    )
                json_input_schema = core_schema.typed_dict_schema(td_fields)
            except Exception:
                pass  # Fall back to generic dict schema

        # 3. Build the core schema
        return core_schema.no_info_plain_validator_function(
            validate,
            # 4. Define how to serialize it back out
            serialization=core_schema.plain_serializer_function_ser_schema(
                # Use your custom to_dict method for serialization
                lambda instance: instance.to_dict(),
                info_arg=False,
                # Tell Pydantic to treat the serialized output as a dictionary
                return_schema=core_schema.dict_schema(),
            ),
            # 5. Provide structured schema for JSON schema generation
            json_schema_input_schema=json_input_schema,
        )


# --------------------------------------------------------------
#                      ValidatedModel
# --------------------------------------------------------------


MISSING = mm.missing


# --------------------------------------------------------------
#                     SchemaModel
# --------------------------------------------------------------


class SchemaModel(DataClassModel):
    _schema_config: ClassVar[dict[str, Any]] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._schema_config.get("attach_schema_hooks", True):
            attach_schema_hooks(cls, cls._schema_config.get("remove_post_load_hooks", True))

    @classmethod
    def from_dict(  # type: ignore[override]
        cls, data: dict[str, Any], partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> Self:
        """deserialize JSON data (and validate)

        Args:
            cls: class type to construct from data
            data (JSONObject): JSON data that will be deserialized
            partial (bool, optional): Whether to partially construct. Defaults to False.

        Returns:
            An instance of the model class
        """
        # return super().from_dict(data, partial=partial, **kwargs)
        return cls.model_schema(partial=partial, **kwargs).load(data=data, partial=partial)  # type: ignore[return-value]

    def to_dict(  # type: ignore[override]
        self, partial: bool = DEFAULT_PARTIAL, validate: bool = DEFAULT_VALIDATE, **kwargs
    ) -> JSONObject:
        model_dict = cast(JSONObject, self.model_schema(partial=partial).dump(self, **kwargs))
        if validate:
            self.validate(model_dict, partial=partial, **kwargs)
        return model_dict

    def update(self, data: dict[str, Any]):
        """Update dataclass attributes with validation"""
        existing_data = self.to_dict(partial=True)
        existing_data.update(data)
        updated_self = self.from_dict(existing_data, partial=True)

        for field in self.get_model_fields():
            new_value = getattr(updated_self, field.name)

            if FieldProps(field).requires_init():
                if new_value is not None or new_value == mm.missing:
                    setattr(self, field.name, new_value)
            else:
                setattr(self, field.name, new_value)

    def validate_obj(self, partial: bool = DEFAULT_PARTIAL, **kwargs):
        self.validate(self, partial=partial, **kwargs)

    @classmethod
    def validate(cls, data: dict[str, Any] | Self, partial: bool = DEFAULT_PARTIAL, **kwargs):
        try:
            if isinstance(data, cls):
                data = data.to_dict(partial=partial)
            cls.from_dict(cast(JSONObject, data), partial=partial)
        except Exception as e:
            raise mm.ValidationError(f"Validation failed for {cls.__name__}: {e}")

    def is_valid_obj(self, partial: bool = DEFAULT_PARTIAL, **kwargs) -> bool:
        return self.is_valid(self, partial=partial, **kwargs)

    @classmethod
    def is_valid(
        cls, data: dict[str, Any] | Self, partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> bool:
        try:
            cls.validate(data, partial=partial, **kwargs)
        except mm.ValidationError:
            return False
        return True

    @classmethod
    def empty(cls) -> Self:
        empty: dict[str, Any] = {}
        return cls.from_dict(empty, partial=True)

    # ----------------------------------------
    # Schema-related fields
    # ----------------------------------------

    @classmethod
    def as_mm_field(cls, partial: bool = DEFAULT_PARTIAL, **kwargs) -> NestedField:
        return NestedField(cls.model_schema(partial=partial, **kwargs))

    @classmethod
    def model_schema(cls, partial: bool = DEFAULT_PARTIAL, **kwargs) -> mm.Schema:
        """Marshmallow Schema representing this class.

        By default, a schema is generated for you.

        """
        return cls.schema(partial=partial, **kwargs)

    # ----------------------------------------
    # Default schema hooks
    # ----------------------------------------

    @classmethod
    @mm.post_load
    def make_object(cls, data: dict[str, Any], partial: bool = DEFAULT_PARTIAL, **kwargs) -> Self:
        """Method for defining how to make an instance based on validated data.

        Args:
            cls (Type[T]): The class of instance to make
            partial (bool, optional): Whether to partially construct. Defaults to False.
            data (dict): Validated data (based on schema)

        Returns:
            An instance of the model
        """
        if partial:
            class_fields = fields(cls)  # type: ignore[arg-type]
            for class_field in class_fields:
                if class_field.name not in data:
                    field_props = FieldProps(class_field)
                    if not field_props.requires_init():
                        continue
                    elif field_props.is_optional_type():
                        data[class_field.name] = None
                    else:
                        # required value. We will do something whacky
                        data[class_field.name] = MISSING

        return cls(**data)  # type: ignore

    @classmethod
    @mm.post_dump
    def remove_optional_values(cls, data: dict, **kwargs) -> dict:
        """Schema post-dump hook which removes optional null values from data

        Args:
            data (dict): self as dict
        """

        class_fields = cls.get_model_fields()
        for class_field in class_fields:
            if class_field.name in data:
                field_props = FieldProps(class_field)
                if field_props.is_optional_type() and data[class_field.name] is None:
                    data.pop(class_field.name)
        return data

    @classmethod
    @mm.post_dump
    def remove_missing_values(cls, data: dict, **kwargs) -> dict:
        """Schema Post dump hook that removes MISSING values from data"""
        new_data = remove_matching_values(data, recursive=True, target_value=MISSING)
        return cast(dict, new_data)

    def is_partial(self) -> bool:
        """Verifies if object is partially defined"""
        for class_field in self.get_model_fields():
            field_props = FieldProps(class_field)
            if not field_props.is_optional_type() and getattr(self, class_field.name) is MISSING:
                return True
        return False

    def copy(self, partial: bool = DEFAULT_PARTIAL, **kwargs) -> Self:
        return self.from_dict(
            data=self.to_dict(partial=partial, **kwargs), partial=partial, **kwargs
        )


class ModelSchemaMethod(Protocol):
    def __call__(
        self, cls: type[SM], partial: bool, **kwargs
    ) -> mm.Schema: ...  # pragma: no cover


class ModelClassMethod(Protocol):
    def __call__(*args, **kwargs) -> Any: ...  # pragma: no cover


def attach_schema_hooks(cls: type[SchemaModel], remove_post_load_hooks: bool = True):  # noqa: C901
    """Attaches schema hooks from SchemaModel class onto the schema class

    Args:
        cls (Type[SchemaModel]): The subclass of schema model
        remove_post_load_hooks (bool): Whether to remove post_load methods from schema.
            Defaults to True.
    """
    MARSHMALLOW_HOOK_ATTR = "__marshmallow_hook__"

    # We must use the underlying __func__ of this method variable in order to pass in
    # the correct class variable. This was problematic for classes that subclassing
    # child classes of SchemaModel.
    # In the following scenario:
    #   B -child-of--> A -child-of--> SchemaModel
    #
    #   B.model_schema() would call the bound method of A.model_schema
    #   because we were wrapping the bound method, not the function
    model_schema_method: ModelSchemaMethod = cls.model_schema.__func__  # type: ignore

    def check_and_attach_schema_hook(
        cls: type[SM],
        schema: mm.Schema,
        class_method_name: str,
        class_method: ModelClassMethod,
    ):
        """Decorates a SchemaModel class method as a mm.Schema hook and attaches to the schema

        Args:
            cls (Type[SchemaModelV1]): subclass of V1 schema model
            schema (mm.Schema): The schema instance of the schema model
            class_method_name (str): name of class method being decorated, attached
            class_method (ModelClassMethod): class method being decorated, attached

        """
        try:
            hook_config = class_method.__marshmallow_hook__  # type: ignore[attr-defined]
        except AttributeError:
            return

        @wraps(class_method)
        def schema_hook(self, *args, **kwargs):
            return class_method(*args, **kwargs)

        setattr(schema_hook, MARSHMALLOW_HOOK_ATTR, hook_config)
        setattr(schema.__class__, f"_{class_method_name}__auto", MethodType(schema_hook, schema))

    @cache
    @wraps(model_schema_method)
    def model_schema_with_hooks(
        cls: type[SM], partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> mm.Schema:
        schema = model_schema_method(cls, partial=partial, **kwargs)

        if remove_post_load_hooks:
            post_load_key = POST_LOAD
            for post_load_method_name, many, args in schema._hooks.get(post_load_key, []):
                try:
                    post_load_method = getattr(schema, post_load_method_name)
                    if hook_attr := getattr(post_load_method, MARSHMALLOW_HOOK_ATTR):
                        # Ignore auto-generated post_load methods
                        if post_load_method_name == f"_{cls.make_object.__name__}__auto":
                            continue
                        hook_attr.pop(post_load_key, None)
                except Exception:
                    pass

        class_methods = inspect.getmembers(cls, predicate=inspect.ismethod)

        for class_method_name, class_method in class_methods:
            check_and_attach_schema_hook(cls, schema, class_method_name, class_method)

        # Lastly, reset hooks of the mm.Schema by re-running `resolve_hooks`
        setattr(schema.__class__, "_hooks", schema.__class__.resolve_hooks())
        return schema

    setattr(cls, "model_schema", MethodType(model_schema_with_hooks, cls))


class BaseSchema(mm.Schema):
    pass


@dataclass
class NONE(SchemaModel):
    """Can be used as a No-op"""
