import datetime as dt
import json
import uuid
from contextlib import nullcontext as does_not_raise
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, ClassVar, Dict, Optional

import marshmallow as mm
import pytest
import yaml
from marshmallow import ValidationError

from aibs_informatics_core.models.base import (
    MISSING,
    BaseModel,
    BaseSchema,
    CustomAwareDateTime,
    DataClassModel,
    FloatField,
    IntegerField,
    SchemaModel,
    StringField,
    UUIDField,
    field_metadata,
)
from aibs_informatics_core.utils.decorators import cache
from aibs_informatics_core.utils.json import JSONObject

# ----------------------------------------------------------
#                       BaseModel tests
# ----------------------------------------------------------


class SimpleBaseModel(BaseModel):
    a_str: str
    a_int: int

    def __init__(self, a_str: str, a_int: int) -> None:
        self.a_str = a_str
        self.a_int = a_int

    def to_dict(self, **kwargs) -> JSONObject:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: JSONObject, **kwargs) -> "SimpleBaseModel":
        return cls(**data)


def test__BaseModel__to_dict__from_dict():
    model = SimpleBaseModel(a_str="I'm a string!", a_int=42)
    assert model.to_dict() == {"a_str": "I'm a string!", "a_int": 42}

    new_model = SimpleBaseModel.from_dict(data={"a_str": "I'm a string!", "a_int": 42})
    assert new_model.a_int == 42
    assert new_model.a_str == "I'm a string!"


def test__BaseModel__to_json__from_json():
    model = SimpleBaseModel(a_str="I'm a string!", a_int=42)
    assert model.to_json() == json.dumps({"a_str": "I'm a string!", "a_int": 42}, indent=4)

    new_model = SimpleBaseModel.from_json(data='{"a_str": "I\'m a string!", "a_int": 42}')
    assert new_model.a_int == 42
    assert new_model.a_str == "I'm a string!"


def test__BaseModel__copy():
    model = SimpleBaseModel(a_str="I'm a string!", a_int=42)
    new_model = model.copy()
    assert new_model.a_int == 42
    assert new_model.a_str == "I'm a string!"
    assert new_model is not model


# ----------------------------------------------------------
#                       DataClassModel tests
# ----------------------------------------------------------


@dataclass
class MyDataClassModel(DataClassModel):
    a_str: str
    a_int: int


def test__DataClassModel__to_dict__from_dict():
    model = MyDataClassModel(a_str="I'm a string!", a_int=42)
    assert model.to_dict() == {"a_str": "I'm a string!", "a_int": 42}

    new_model = MyDataClassModel.from_dict(data={"a_str": "I'm a string!", "a_int": 42})
    assert new_model == model


def test__DataClassModel__to_json__from_json():
    model = MyDataClassModel(a_str="I'm a string!", a_int=42)
    assert model.to_json() == json.dumps({"a_str": "I'm a string!", "a_int": 42}, indent=4)

    new_model = MyDataClassModel.from_json(data='{"a_str": "I\'m a string!", "a_int": 42}')
    assert new_model == model


def test__DataClassModel__get_model_fields():
    model_fields = MyDataClassModel.get_model_fields()

    assert len(model_fields) == 2
    assert model_fields[0].name == "a_str"
    assert model_fields[1].name == "a_int"


# ----------------------------------------------------------
#          SchemaModel tests (with explicit schema)
# ----------------------------------------------------------


class MockEntrySchema(BaseSchema):
    a_uuid = UUIDField(required=True)
    a_timestamp = CustomAwareDateTime(format="iso8601", required=True)
    a_str = StringField(required=True)
    a_float = FloatField(required=True)
    a_int = IntegerField(required=True)


@dataclass
class MockEntry(SchemaModel):
    a_uuid: uuid.UUID
    a_timestamp: dt.datetime
    a_str: str
    a_float: float
    a_int: int

    @classmethod
    @cache
    def model_schema(cls, many: bool = False, partial: bool = False, **kwargs) -> BaseSchema:
        return MockEntrySchema(many=many, partial=partial)


class HasOptionalFieldSchema(BaseSchema):
    required_str = StringField(required=True)
    optional_str = StringField(required=False, allow_none=True)


@dataclass
class HasOptionalField(SchemaModel):
    required_str: str
    optional_str: Optional[str] = None

    @classmethod
    def model_schema(cls, many: bool = False, partial: bool = False, **kwargs) -> BaseSchema:
        return HasOptionalFieldSchema(many=many, partial=partial)


@pytest.mark.parametrize(
    "model_class, input_data, partial, raise_expectation, expected",
    [
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": "I'm a string!",
                "a_float": 3.1415,
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
                a_str="I'm a string!",
                a_float=3.1415,
                a_int=42,
            ),
            id="All input data valid",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "I'm a bogus uuid :( dfe7b672-91e0-4c2d-ac06",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": "I'm a string!",
                "a_float": 3.1415,
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid UUID"),
            # expected
            None,
            id="Invalid uuid",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11",
                "a_str": "I'm a string!",
                "a_float": 3.1415,
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid datetime"),
            # expected
            None,
            id="Invalid timestamp",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": -42,
                "a_float": 3.1415,
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid string"),
            # expected
            None,
            id="invalid str",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": "I'm a string!",
                "a_float": "Not a float!",
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid number"),
            # expected
            None,
            id="Invalid float",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": "I'm a string!",
                "a_float": 3.1415,
                "a_int": "Not an int!",
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid int"),
            # expected
            None,
            id="Invalid int",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_str": "I'm a string!",
                "a_int": 42,
            },
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Missing data for required field."),
            # expected
            None,
            id="Load partial data without partial=True fails",
        ),
        pytest.param(
            # model_class
            MockEntry,
            # input_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_str": "I'm a string!",
                "a_int": 42,
            },
            # partial
            True,
            # raise_expectation
            does_not_raise(),
            # expected
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=MISSING,
                a_float=MISSING,
                a_str="I'm a string!",
                a_int=42,
            ),
            id="Load partial data with partial=True succeeds",
        ),
        pytest.param(
            # model_class
            HasOptionalField,
            # input_data
            {"optional_str": "I'm optional!", "required_str": "I'm required!"},
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            HasOptionalField(optional_str="I'm optional!", required_str="I'm required!"),
            id="Loading when all fields are present",
        ),
        pytest.param(
            # model_class
            HasOptionalField,
            # input_data
            {"required_str": "I'm required!"},
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            HasOptionalField(required_str="I'm required!"),
            id="Test when optional missing",
        ),
        pytest.param(
            # model_class
            HasOptionalField,
            # input_data
            {"optional_str": "I'm optional!"},
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError, match="Missing data for required field."),
            # expected
            None,
            id="Test when required missing but optional present",
        ),
    ],
)
def test__SchemaModel__with_explicit_model_schema__from_dict(
    model_class, input_data, partial, raise_expectation, expected
):
    with raise_expectation:
        obt = model_class.from_dict(data=input_data, partial=partial)

    if expected is not None:
        assert expected == obt


@pytest.mark.parametrize(
    "model_to_update, update_data, raise_expectation, expected",
    [
        pytest.param(
            # model_to_update
            MockEntry.empty(),
            # update_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_str": "update string",
            },
            # raise_expectation
            does_not_raise(),
            # expected
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=MISSING,
                a_str="update string",
                a_float=MISSING,
                a_int=MISSING,
            ),
            id="A valid update",
        ),
        pytest.param(
            # model_to_update
            MockEntry(
                a_uuid=uuid.UUID("21c01c0c-d4c1-40c7-b118-19f0878ade62"),
                a_timestamp=MISSING,
                a_str="some initial value",
                a_float=MISSING,
                a_int=42,
            ),
            # update_data
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_str": "some new value",
            },
            # raise_expectation
            does_not_raise(),
            # expected
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=MISSING,
                a_str="some new value",
                a_float=MISSING,
                a_int=42,
            ),
            id="Valid update that updates some, but not all, existing values",
        ),
        pytest.param(
            # model_to_update
            MockEntry(
                a_uuid=MISSING,
                a_timestamp=MISSING,
                a_str=MISSING,
                a_float=MISSING,
                a_int=MISSING,
            ),
            # update_data
            {
                "a_uuid": "Woops I'm not a valid uuid ac06-30dd1ac2eb96",
            },
            # raise_expectation
            pytest.raises(ValidationError),
            # expected
            None,
            id="An invalid update",
        ),
        pytest.param(
            # model_to_update
            MockEntry(
                a_uuid=MISSING,
                a_timestamp=MISSING,
                a_str="Hope I don't get overwritten",
                a_float=MISSING,
                a_int=42,
            ),
            # update_data
            {
                "a_str": "I'm a valid update but...",
                "a_int": "I'm not valid, will 'a_str' get overwritten?",
            },
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid int"),
            # expected
            MockEntry(
                a_uuid=MISSING,
                a_timestamp=MISSING,
                a_str="Hope I don't get overwritten",
                a_float=MISSING,
                a_int=42,
            ),
            id="Invalid update, test existing data does not get overwritten",
        ),
    ],
)
def test__SchemaModel__with_explicit_model_schema__update(
    model_to_update, update_data, raise_expectation, expected
):
    with raise_expectation:
        model_to_update.update(data=update_data)

    if expected is not None:
        assert expected == model_to_update


@pytest.mark.parametrize(
    "model_to_dump, partial, raise_expectation, expected",
    [
        pytest.param(
            # model_to_dump
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
                a_str="I'm a string!",
                a_float=3.1415,
                a_int=42,
            ),
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            {
                "a_uuid": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                "a_timestamp": "2022-03-11T08:23:51.248794+00:00",
                "a_str": "I'm a string!",
                "a_float": 3.1415,
                "a_int": 42,
            },
            id="Dumps without issues",
        ),
        pytest.param(
            # model_to_dump
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
                a_str="Missing a_float!!",
                a_float=None,
                a_int=42,
            ),
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError),
            # expected
            None,
            id="Dump with partial data fails when partial=False",
        ),
        pytest.param(
            # model_to_dump
            MockEntry(
                a_uuid=MISSING,
                a_timestamp=MISSING,
                a_str="I'm a string!",
                a_float=3.1415,
                a_int=42,
            ),
            # partial
            True,
            # raise_expectation
            does_not_raise(),
            # expected
            {"a_str": "I'm a string!", "a_float": 3.1415, "a_int": 42},
            id="Dump with partial succeeds when partial=True",
        ),
        pytest.param(
            # model_to_dump
            HasOptionalField(optional_str="I'm optional!", required_str="I'm required!"),
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            {"optional_str": "I'm optional!", "required_str": "I'm required!"},
            id="Dumping when all fields present",
        ),
        pytest.param(
            # model_to_dump
            HasOptionalField(required_str="I'm required!"),
            # partial
            False,
            # raise_expectation
            does_not_raise(),
            # expected
            {"required_str": "I'm required!"},
            id="Dumping when optional missing",
        ),
        pytest.param(
            # model_to_dump
            HasOptionalField(required_str=None, optional_str="I'm optional!"),
            # partial
            False,
            # raise_expectation
            pytest.raises(ValidationError),
            # expected
            None,
            id="Dumping when required missing but optional present",
        ),
    ],
)
def test__SchemaModel__with_explicit_model_schema__to_dict(
    model_to_dump, partial, raise_expectation, expected
):
    with raise_expectation:
        obtained = model_to_dump.to_dict(partial=partial)

    if expected is not None:
        assert expected == obtained


@pytest.mark.parametrize(
    "model_to_set, attr_value, raise_expectation, expected",
    [
        pytest.param(
            # model_to_set
            MockEntry(
                a_uuid=None,
                a_timestamp=None,
                a_str="I'm a string!",
                a_float=None,
                a_int=None,
            ),
            # attr_value
            ("a_str", "I'm a new string"),
            # raise_expectation
            does_not_raise(),
            # expected
            MockEntry(
                a_uuid=None,
                a_timestamp=None,
                a_str="I'm a new string",
                a_float=None,
                a_int=None,
            ),
            id="Basic set attr succeeds",
        ),
        pytest.param(
            # model_to_set
            MockEntry(
                a_uuid=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                a_timestamp=None,
                a_str=None,
                a_float=None,
                a_int=None,
            ),
            # attr_value
            ("a_uuid", "ab8933eb-7594-4a5e-8d5f-f9384bbef784"),
            # raise_expectation
            does_not_raise(),
            # expected
            # NOTE: a_uuid is now a STRING instead of a uuid.UUID
            #       mypy typing WILL COMPLAIN.
            MockEntry(
                a_uuid="ab8933eb-7594-4a5e-8d5f-f9384bbef784",  # type: ignore
                a_timestamp=None,
                a_str=None,
                a_float=None,
                a_int=None,
            ),  # type: ignore
            id="Setting an attr does NOT auto convert for complex types",
        ),
    ],
)
def test__SchemaModel__with_explicit_model_schema__setattr(
    model_to_set, attr_value, raise_expectation, expected
):
    with raise_expectation:
        setattr(model_to_set, *attr_value)

    if expected is not None:
        assert expected == model_to_set


# ----------------------------------------------------------
#                       SchemaModel tests
# ----------------------------------------------------------


@dataclass
class Empty(SchemaModel):
    pass


@dataclass
class Simple(SchemaModel):
    str_value: str
    int_value: int


@dataclass
class SimpleChild(Simple):
    bool_value: bool


@dataclass
class SimpleNested(SchemaModel):
    empty_sm: Empty
    required_simple: Simple
    optional_simple: Optional[Simple] = None


@dataclass
class Complex(SchemaModel):
    uuid_value: uuid.UUID = field(metadata=field_metadata(mm_field=UUIDField()))
    dt_value: dt.datetime = field(
        metadata=field_metadata(mm_field=CustomAwareDateTime(format="iso8601", required=True))
    )
    alternate_dt_value: dt.datetime = field(
        metadata=field_metadata(encoder=dt.datetime.isoformat, decoder=dt.datetime.fromisoformat)
    )


@dataclass
class ComplexNested(SchemaModel):
    required: Complex
    optional: Optional[Complex] = None


def test__SchemaModel__auto():
    @dataclass
    class ModelWithNoSchemaHooks(SchemaModel):
        str_val: str
        int_val: int

        _schema_config: ClassVar[Dict[str, Any]] = {
            "attach_schema_hooks": False,
            "remove_post_load_hooks": True,
        }

        @classmethod
        @mm.pre_dump
        def no_op(cls, obj, **kwargs):
            return obj

    @dataclass
    class ModelWithSchemaHooks(ModelWithNoSchemaHooks):
        _schema_config: ClassVar[Dict[str, Any]] = {
            "attach_schema_hooks": True,
            "remove_post_load_hooks": True,
        }

    no_hooks_schema = ModelWithNoSchemaHooks.model_schema()
    with_hooks_schema = ModelWithSchemaHooks.model_schema()

    for key, expected1, expected2 in [
        (("pre_load", False), [], []),
        (("post_load", False), ["make_modelwithnoschemahooks"], ["_make_object__auto"]),
        (("pre_dump", False), [], ["_no_op__auto"]),
        (
            ("post_dump", False),
            [],
            ["_remove_missing_values__auto", "_remove_optional_values__auto"],
        ),
    ]:
        assert no_hooks_schema._hooks[key] == expected1
        assert with_hooks_schema._hooks[key] == expected2


@pytest.mark.parametrize(
    "model,expected_json,raise_exception",
    [
        # Valid cases
        pytest.param(
            Empty(),
            {},
            does_not_raise(),
            id=f"{Empty.__name__}",
        ),
        pytest.param(
            Simple("str", 1),
            {"str_value": "str", "int_value": 1},
            does_not_raise(),
            id=f"{Simple.__name__}",
        ),
        pytest.param(
            SimpleChild("str", 1, True),
            {"str_value": "str", "int_value": 1, "bool_value": True},
            does_not_raise(),
            id=f"{SimpleChild.__name__}",
        ),
        pytest.param(
            SimpleNested(Empty(), Simple("str", 1)),
            {
                "empty_sm": {},
                "required_simple": {"str_value": "str", "int_value": 1},
            },
            does_not_raise(),
            id=f"{SimpleNested.__name__}",
        ),
        pytest.param(
            ComplexNested(
                Complex(
                    uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                    dt.datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
                    dt.datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
                )
            ),
            {
                "required": {
                    "uuid_value": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                    "dt_value": "2022-03-11T08:23:51.248794+00:00",
                    "alternate_dt_value": "2022-03-11T08:23:51.248794+00:00",
                },
            },
            does_not_raise(),
            id=f"{ComplexNested.__name__}",
        ),
        # Invalid cases
        pytest.param(
            Simple("str", "abc"),  # type: ignore
            None,
            pytest.raises((ValidationError, ValueError)),
            id=f"{Simple.__name__} has invalid values",
        ),
        pytest.param(
            SimpleNested(Empty(), Simple("str", "abc")),  # type: ignore
            None,
            pytest.raises((ValidationError, ValueError)),
            id=f"{SimpleNested.__name__} has invalid nested values",
        ),
    ],
)
def test__SchemaModel__to_dict(model, expected_json, raise_exception):
    with raise_exception:
        actual_json = model.to_dict()

    if expected_json:
        assert actual_json == expected_json


@pytest.mark.parametrize(
    "model_cls, model_json,expected_model,raise_exception",
    [
        pytest.param(
            Empty,
            {},
            Empty(),
            does_not_raise(),
            id=f"{Empty.__name__}",
        ),
        pytest.param(
            Simple,
            {"str_value": "str", "int_value": 1},
            Simple("str", 1),
            does_not_raise(),
            id=f"{Simple.__name__}",
        ),
        pytest.param(
            SimpleChild,
            {"str_value": "str", "int_value": 1, "bool_value": True},
            SimpleChild("str", 1, True),
            does_not_raise(),
            id=f"{SimpleChild.__name__}",
        ),
        pytest.param(
            SimpleNested,
            {
                "empty_sm": {},
                "required_simple": {"str_value": "str", "int_value": 1},
                "optional_simple": None,
            },
            SimpleNested(Empty(), Simple("str", 1)),
            does_not_raise(),
            id=f"{SimpleNested.__name__}",
        ),
        pytest.param(
            ComplexNested,
            {
                "required": {
                    "uuid_value": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                    "dt_value": "2022-03-11T08:23:51.248794+00:00",
                    "alternate_dt_value": "2022-03-11T08:23:51.248794+00:00",
                },
                "optional": None,
            },
            ComplexNested(
                Complex(
                    uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                    dt.datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
                    dt.datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
                )
            ),
            does_not_raise(),
            id=f"{ComplexNested.__name__}",
        ),
        # Invalid cases
        pytest.param(
            Simple,
            {"str_value": 1, "int_value": 1},
            None,
            pytest.raises(ValidationError),
            id=f"{Simple.__name__} has incorrect field type",
        ),
        pytest.param(
            SimpleNested,
            {
                "empty_sm": {},
                "required_simple": None,
                "optional_simple": {"str_value": "str", "int_value": 1},
            },
            None,
            pytest.raises(ValidationError),
            id=f"{SimpleNested.__name__} missing required field",
        ),
        pytest.param(
            SimpleNested,
            {"empty_sm": [1], "required_simple": {"str_value": "str", "int_value": 1}},
            None,
            pytest.raises(ValidationError),
            id=f"{SimpleNested.__name__} incorrect field type",
        ),
        pytest.param(
            SimpleNested,
            {
                "empty_sm": {},
                "optional_simple": None,
                "required_simple": {"str_value": 123, "int_value": "abc"},
            },
            None,
            pytest.raises(ValidationError),
            id=f"{SimpleNested.__name__} incorrect nested field type",
        ),
    ],
)
def test__SchemaModel__from_dict(model_cls, model_json, expected_model, raise_exception):
    with raise_exception:
        actual_model = model_cls.from_dict(model_json)
    if expected_model:
        assert actual_model == expected_model


def test__SchemaModel__from_path__json_file():
    model = Simple(int_value=1, str_value="s")
    model_dict = model.to_dict()
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model.json"
        path.write_text(json.dumps(model_dict))

        new_model = Simple.from_path(path)
    assert new_model == model


def test__SchemaModel__from_path__yaml_file():
    model = Simple(int_value=1, str_value="s")
    model_dict = model.to_dict()
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model.yaml"
        path.write_text(yaml.safe_dump(model_dict))

        new_model = Simple.from_path(path)
    assert new_model == model


def test__SchemaModel__to_path__from_path():
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model"
        model = Simple(int_value=1, str_value="s")
        model.to_path(path)
        new_model = Simple.from_path(path)
    assert new_model == model


def test__SchemaModel__is_partial():
    model = Simple.empty()
    assert model.is_partial()

    model = Simple(int_value=1, str_value="s")
    assert not model.is_partial()


def test__SchemaModel__validate_obj():
    model = Simple(int_value=1, str_value="s")
    model.validate_obj()

    model = Simple(int_value=1, str_value="s")
    model.int_value = "s"
    with pytest.raises(ValidationError):
        model.validate_obj()


def test__SchemaModel__is_valid():
    data = dict(int_value=1, str_value="s")
    assert Simple.is_valid(data)

    assert not Simple.is_valid({})
