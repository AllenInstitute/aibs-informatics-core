__all__ = [
    "ModelProtocol",
    "ModelBase",
    "BaseSchema",
    "DataClassModel",
    "MISSING",
    "NONE",
    "SchemaModel",
    "WithValidation",
    "post_dump",
    "pre_dump",
    "pre_load",
    "validates_schema",
]

import abc
import inspect
import json
from dataclasses import MISSING as dataclass_MISSING
from dataclasses import Field, dataclass, fields
from functools import wraps
from pathlib import Path
from types import MethodType
from typing import (
    Any,
    ClassVar,
    Dict,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
    runtime_checkable,
)

import marshmallow as mm
import yaml  # type: ignore[import-untyped]
from dataclasses_json import DataClassJsonMixin, Undefined, config
from dataclasses_json.core import _ExtendedEncoder
from marshmallow import post_dump, pre_dump, pre_load, validates_schema
from marshmallow.decorators import POST_LOAD

from aibs_informatics_core.models.base.custom_fields import NestedField
from aibs_informatics_core.models.base.field_utils import FieldProps
from aibs_informatics_core.utils.decorators import cache
from aibs_informatics_core.utils.json import JSONObject
from aibs_informatics_core.utils.tools.dicttools import remove_matching_values

T = TypeVar("T")


DEFAULT_PARTIAL = False
DEFAULT_VALIDATE = True

M = TypeVar("M", bound="ModelBase")
DCM = TypeVar("DCM", bound="DataClassModel")
SM = TypeVar("SM", bound="SchemaModel")


# --------------------------------------------------------------
#                             ModelProtocol
# --------------------------------------------------------------


@runtime_checkable
class ModelProtocol(Protocol):
    @classmethod
    def from_dict(cls: Type[T], data: JSONObject, **kwargs) -> T:
        ...  # pragma: no cover

    def to_dict(self, **kwargs) -> JSONObject:
        ...  # pragma: no cover

    @classmethod
    def from_json(cls: Type[T], data: str, **kwargs) -> T:
        ...  # pragma: no cover

    def to_json(self, **kwargs) -> str:
        ...  # pragma: no cover

    @classmethod
    def from_path(cls: Type[T], path: Path, **kwargs) -> T:
        ...  # pragma: no cover

    def to_path(self, path: Path, **kwargs):
        ...  # pragma: no cover


# --------------------------------------------------------------
#                             BaseModel ABC
# --------------------------------------------------------------


class ModelBase:
    @classmethod
    @abc.abstractmethod
    def from_dict(cls: Type[M], data: JSONObject, **kwargs) -> M:
        raise NotImplementedError(
            f"Must implement this method in {cls.__name__}"
        )  # pragma: no cover

    @abc.abstractmethod
    def to_dict(self, **kwargs) -> JSONObject:
        raise NotImplementedError(
            f"Must implement this method in {self.__class__.__name__}"
        )  # pragma: no cover

    @classmethod
    def from_json(cls: Type[M], data: str, **kwargs) -> M:
        return cls.from_dict(json.loads(data), **kwargs)

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(**kwargs), indent=4)

    @classmethod
    def from_path(cls: Type[M], path: Path, **kwargs) -> M:
        if path.suffix in (".yml", ".yaml"):
            path.read_text()
            with open(path, "r") as f:
                return cls.from_dict(yaml.safe_load(f), **kwargs)
        else:
            return cls.from_dict(json.loads(path.read_text()), **kwargs)

    def to_path(self, path: Path, **kwargs):
        path.write_text(self.to_json(**kwargs))


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
        cls: Type[DCM], data: JSONObject, partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> DCM:
        return super().from_dict(data, infer_missing=partial)

    def to_dict(self, partial: bool = DEFAULT_PARTIAL, **kwargs) -> JSONObject:  # type: ignore[override]
        return super().to_dict(encode_json=kwargs.get("encode_json", True))

    @classmethod
    def from_json(cls: Type[DCM], data: str, **kwargs) -> DCM:  # type: ignore[override]
        return cls.from_dict(json.loads(data), **kwargs)

    def to_json(self, **kwargs) -> str:
        json_encoder_cls: Type[json.JSONEncoder] = kwargs.pop("json_encoder", _ExtendedEncoder)
        return json.dumps(self.to_dict(**kwargs), indent=4, cls=json_encoder_cls)

    @classmethod
    @cache
    def get_model_fields(cls) -> Tuple[Field, ...]:
        resolved: Optional[Dict[str, Type]] = None
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


# --------------------------------------------------------------
#                      ValidatedModel
# --------------------------------------------------------------


MISSING = mm.missing


class WithValidation:
    """Provides Validations for model for (/de-)serialization"""

    @classmethod
    @abc.abstractmethod
    def validate(cls, data: Dict[str, Any], partial: bool = DEFAULT_PARTIAL, **kwargs):
        raise NotImplementedError("Must implement")  # pragma: no cover


# --------------------------------------------------------------
#                     SchemaModel
# --------------------------------------------------------------


class SchemaModel(DataClassModel):
    _schema_config: ClassVar[Dict[str, Any]] = {}

    def __init_subclass__(cls: Type[SM], **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._schema_config.get("attach_schema_hooks", True):
            attach_schema_hooks(cls, cls._schema_config.get("remove_post_load_hooks", True))

    @classmethod
    def from_dict(  # type: ignore[override]
        cls: Type[SM], data: Dict[str, Any], partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> SM:
        """deserialize JSON data (and validate)

        Args:
            cls (Type[SM]): class type to construct from data
            data (JSONObject): JSON data that will be deserialized
            partial (bool, optional): Whether to partially construct. Defaults to False.

        Returns:
            SM: _description_
        """
        # return super().from_dict(data, partial=partial, **kwargs)
        return cast(
            SM, cls.model_schema(partial=partial, **kwargs).load(data=data, partial=partial)
        )

    def to_dict(  # type: ignore[override]
        self, partial: bool = DEFAULT_PARTIAL, validate: bool = DEFAULT_VALIDATE, **kwargs
    ) -> JSONObject:
        model_dict = cast(JSONObject, self.model_schema(partial=partial).dump(self, **kwargs))
        if validate:
            self.validate(model_dict, partial=partial, **kwargs)
        return model_dict

    def update(self, data: Dict[str, Any]):
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
    def validate(
        cls: Type[SM], data: Union[Dict[str, Any], SM], partial: bool = DEFAULT_PARTIAL, **kwargs
    ):
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
        cls: Type[SM], data: Union[Dict[str, Any], SM], partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> bool:
        try:
            cls.validate(data, partial=partial, **kwargs)
        except mm.ValidationError:
            return False
        return True

    @classmethod
    def empty(cls: Type[SM]) -> SM:
        empty: Dict[str, Any] = {}
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
    def make_object(
        cls: Type[T], data: Dict[str, Any], partial: bool = DEFAULT_PARTIAL, **kwargs
    ) -> T:
        """Method for defining how to make an instance based on validated data.

        Args:
            cls (Type[T]): The class of instance to make
            partial (bool, optional): Whether to partially construct. Defaults to False.
            data (dict): Validated data (based on schema)

        Returns:
            T: An instance of the model
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

    def copy(self: SM, partial: bool = DEFAULT_PARTIAL, **kwargs) -> SM:
        return self.from_dict(
            data=self.to_dict(partial=partial, **kwargs), partial=partial, **kwargs
        )


class ModelSchemaMethod(Protocol):
    def __call__(self, cls: Type[SM], partial: bool, **kwargs) -> mm.Schema:
        ...  # pragma: no cover


class ModelClassMethod(Protocol):
    def __call__(*args, **kwargs) -> Any:
        ...  # pragma: no cover


def attach_schema_hooks(cls: Type[SchemaModel], remove_post_load_hooks: bool = True):
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
        cls: Type[SM],
        schema: mm.Schema,
        class_method_name: str,
        class_method: ModelClassMethod,
    ):
        """Decorates a SchemaModel class method as a mm.Schema hook and attaches to the schema

        Args:
            cls (Type[SM]): subclass of schema model
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
        cls: Type[SM], partial: bool = DEFAULT_PARTIAL, **kwargs
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
                except:
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
