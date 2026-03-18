import datetime as dt
import json
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml
from pydantic import BaseModel

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.base import (
    IsoDate,
    IsoDateTime,
    ModelBase,
    ModelProtocol,
    PydanticBaseModel,
)
from aibs_informatics_core.utils.json import JSONObject

# ===========================================================
#                       ModelBase tests
# ===========================================================


class SimpleBaseModel(ModelBase):
    """Concrete ModelBase subclass used to test inherited helpers."""

    a_str: str
    a_int: int

    def __init__(self, a_str: str, a_int: int) -> None:
        self.a_str = a_str
        self.a_int = a_int

    def to_dict(self, **kwargs) -> JSONObject:
        return {"a_str": self.a_str, "a_int": self.a_int}

    @classmethod
    def from_dict(cls, data: JSONObject, **kwargs) -> "SimpleBaseModel":
        return cls(**data)

    def __eq__(self, other):
        if not isinstance(other, SimpleBaseModel):
            return NotImplemented
        return self.a_str == other.a_str and self.a_int == other.a_int


# --- to_dict / from_dict ---


def test__ModelBase__to_dict__from_dict():
    model = SimpleBaseModel(a_str="I'm a string!", a_int=42)
    assert model.to_dict() == {"a_str": "I'm a string!", "a_int": 42}

    new_model = SimpleBaseModel.from_dict(data={"a_str": "I'm a string!", "a_int": 42})
    assert new_model.a_int == 42
    assert new_model.a_str == "I'm a string!"


# --- to_json / from_json ---


def test__ModelBase__to_json__from_json():
    model = SimpleBaseModel(a_str="I'm a string!", a_int=42)
    assert model.to_json() == json.dumps({"a_str": "I'm a string!", "a_int": 42}, indent=4)

    new_model = SimpleBaseModel.from_json(data='{"a_str": "I\'m a string!", "a_int": 42}')
    assert new_model.a_int == 42
    assert new_model.a_str == "I'm a string!"


# --- from_path (JSON) ---

# ===========================================================
#                   PydanticBaseModel tests
# ===========================================================


class SimplePydanticModel(PydanticBaseModel):
    str_value: str
    int_value: int


class SimplePydanticChild(SimplePydanticModel):
    bool_value: bool


class HasOptionalField(PydanticBaseModel):
    required_str: str
    optional_str: str | None = None


class SimpleNested(PydanticBaseModel):
    required_simple: SimplePydanticModel
    optional_simple: SimplePydanticModel | None = None


class SimpleCollection(PydanticBaseModel):
    simples: list[SimplePydanticModel]


class ComplexModel(PydanticBaseModel):
    uuid_value: uuid.UUID
    dt_value: IsoDateTime
    date_value: IsoDate


class ComplexNested(PydanticBaseModel):
    required: ComplexModel
    optional: ComplexModel | None = None


# --- to_dict / from_dict  (basic) ---


def test__PydanticBaseModel__to_dict__from_dict():
    model = SimplePydanticModel(str_value="I'm a string!", int_value=42)
    d = model.to_dict()
    # Serialization uses snake_case field names (by_alias is not set)
    assert d == {"str_value": "I'm a string!", "int_value": 42}

    # from_dict should accept snake_case
    new_model = SimplePydanticModel.from_dict(d)
    assert new_model == model


def test__PydanticBaseModel__from_dict__accepts_snake_case():
    """populate_by_name=True lets us use the Python field name too."""
    model = SimplePydanticModel.from_dict({"str_value": "hello", "int_value": 7})
    assert model.str_value == "hello"
    assert model.int_value == 7


def test__PydanticBaseModel__from_dict__accepts_camelCase():
    """validation_alias=to_camel allows camelCase input."""
    model = SimplePydanticModel.from_dict({"strValue": "hello", "intValue": 7})
    assert model.str_value == "hello"
    assert model.int_value == 7


# --- to_json / from_json ---


def test__PydanticBaseModel__to_json__from_json():
    model = SimplePydanticModel(str_value="I'm a string!", int_value=42)
    json_str = model.to_json()
    parsed = json.loads(json_str)
    assert parsed == {"str_value": "I'm a string!", "int_value": 42}

    new_model = SimplePydanticModel.from_json(json_str)
    assert new_model == model


# --- exclude_none default ---


def test__PydanticBaseModel__to_dict__excludes_none_by_default():
    model = HasOptionalField(required_str="I'm required!")
    d = model.to_dict()
    assert "optional_str" not in d
    assert d == {"required_str": "I'm required!"}


def test__PydanticBaseModel__to_dict__includes_none_when_requested():
    model = HasOptionalField(required_str="req")
    d = model.to_dict(exclude_none=False)
    assert d["optional_str"] is None


# --- extra fields ignored ---


def test__PydanticBaseModel__extra_fields_ignored():
    model = SimplePydanticModel.from_dict(
        {"str_value": "s", "int_value": 1, "extra_field": "ignored"}
    )
    assert model.str_value == "s"
    assert model.int_value == 1
    assert not hasattr(model, "extra_field")


# --- optional field present ---


def test__PydanticBaseModel__optional_field_present():
    model = HasOptionalField.from_dict({"required_str": "req", "optional_str": "opt"})
    assert model.required_str == "req"
    assert model.optional_str == "opt"


# --- child model ---


def test__PydanticBaseModel__child__to_dict__from_dict():
    model = SimplePydanticChild(str_value="str", int_value=1, bool_value=True)
    d = model.to_dict()
    assert d == {"str_value": "str", "int_value": 1, "bool_value": True}

    new_model = SimplePydanticChild.from_dict(d)
    assert new_model == model


# --- nested models ---


@pytest.mark.parametrize(
    "model, expected_dict",
    [
        pytest.param(
            SimpleNested(
                required_simple=SimplePydanticModel(str_value="s", int_value=1),
            ),
            {
                "required_simple": {"str_value": "s", "int_value": 1},
            },
            id="nested-required-only",
        ),
        pytest.param(
            SimpleNested(
                required_simple=SimplePydanticModel(str_value="s", int_value=1),
                optional_simple=SimplePydanticModel(str_value="o", int_value=2),
            ),
            {
                "required_simple": {"str_value": "s", "int_value": 1},
                "optional_simple": {"str_value": "o", "int_value": 2},
            },
            id="nested-with-optional",
        ),
    ],
)
def test__PydanticBaseModel__nested__to_dict(model, expected_dict):
    assert model.to_dict() == expected_dict


def test__PydanticBaseModel__nested__from_dict():
    data = {
        "required_simple": {"str_value": "s", "int_value": 1},
        "optional_simple": None,
    }
    model = SimpleNested.from_dict(data)
    assert model.required_simple == SimplePydanticModel(str_value="s", int_value=1)
    assert model.optional_simple is None


# --- collection field ---


def test__PydanticBaseModel__collection__to_dict__from_dict():
    model = SimpleCollection(
        simples=[
            SimplePydanticModel(str_value="s1", int_value=1),
            SimplePydanticModel(str_value="s2", int_value=2),
        ]
    )
    d = model.to_dict()
    assert d == {
        "simples": [
            {"str_value": "s1", "int_value": 1},
            {"str_value": "s2", "int_value": 2},
        ],
    }
    new_model = SimpleCollection.from_dict(d)
    assert new_model == model


# --- complex types (UUID, IsoDateTime, IsoDate) ---


def test__PydanticBaseModel__complex__to_dict__from_dict():
    model = ComplexModel(
        uuid_value=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
        dt_value=dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
        date_value=dt.date(2022, 3, 11),
    )
    d = model.to_dict()

    assert d["uuid_value"] == "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"
    assert d["dt_value"] == "2022-03-11T08:23:51.248794Z"
    assert d["date_value"] == "2022-03-11"

    new_model = ComplexModel.from_dict(d)
    assert new_model == model


def test__PydanticBaseModel__complex_nested__to_dict__from_dict():
    inner = ComplexModel(
        uuid_value=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
        dt_value=dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
        date_value=dt.date(2022, 3, 11),
    )
    model = ComplexNested(required=inner)
    d = model.to_dict()

    assert d == {
        "required": {
            "uuid_value": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
            "dt_value": "2022-03-11T08:23:51.248794Z",
            "date_value": "2022-03-11",
        },
    }
    new_model = ComplexNested.from_dict(d)
    assert new_model == model


# --- IsoDateTime custom parsing ---


@pytest.mark.parametrize(
    "raw_input, expected_dt",
    [
        pytest.param(
            "2022-03-11T08:23:51.248794+00:00",
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
            id="iso8601-with-tz",
        ),
        pytest.param(
            "2022-03-11T08:23:51.0",
            dt.datetime(2022, 3, 11, 8, 23, 51),
            id="iso-with-fractional-zero",
        ),
    ],
)
def test__IsoDateTime__parsing(raw_input, expected_dt):
    class DtModel(PydanticBaseModel):
        ts: IsoDateTime

    model = DtModel.from_dict({"ts": raw_input})
    assert model.ts == expected_dt


def test__IsoDate__parsing():
    class DateModel(PydanticBaseModel):
        d: IsoDate

    model = DateModel.from_dict({"d": "2022-03-11"})
    assert model.d == dt.date(2022, 3, 11)


# --- from_path / to_path (inherited from ModelBase) ---


def test__PydanticBaseModel__from_path__json_file():
    model = SimplePydanticModel(str_value="s", int_value=1)
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model.json"
        path.write_text(json.dumps(model.to_dict()))

        new_model = SimplePydanticModel.from_path(path)
    assert new_model == model


def test__PydanticBaseModel__from_path__yaml_file():
    model = SimplePydanticModel(str_value="s", int_value=1)
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model.yaml"
        path.write_text(yaml.safe_dump(model.to_dict()))

        new_model = SimplePydanticModel.from_path(path)
    assert new_model == model


def test__PydanticBaseModel__to_path__from_path():
    model = SimplePydanticModel(str_value="s", int_value=1)
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model"
        model.to_path(path)
        new_model = SimplePydanticModel.from_path(path)
    assert new_model == model


# --- validation errors ---


@pytest.mark.parametrize(
    "model_cls, data, match",
    [
        pytest.param(
            SimplePydanticModel,
            {"str_value": "s"},
            "intValue",
            id="missing-required-field",
        ),
        pytest.param(
            SimplePydanticModel,
            {"str_value": "s", "int_value": "not-an-int"},
            "int_parsing",
            id="invalid-int-value",
        ),
        pytest.param(
            SimpleNested,
            {"required_simple": None},
            "required_simple",
            id="nested-required-none",
        ),
    ],
)
def test__PydanticBaseModel__from_dict__validation_errors(model_cls, data, match):
    with pytest.raises(ValidationError, match=match):
        model_cls.from_dict(data)


# --- ModelProtocol conformance ---


def test__PydanticBaseModel__satisfies_ModelProtocol():
    assert isinstance(SimplePydanticModel(str_value="x", int_value=0), ModelProtocol)


# ===========================================================
#               Pydantic + native BaseModel nesting
# ===========================================================


class SimpleNativePydanticModel(BaseModel):
    str_value: str
    int_value: int


class PydanticNestedMixedModel(PydanticBaseModel):
    pydantic_model: SimplePydanticModel
    native_pydantic_model: SimpleNativePydanticModel


def test__PydanticNestedMixedModel__to_dict__from_dict():
    model = PydanticNestedMixedModel(
        pydantic_model=SimplePydanticModel(str_value="s", int_value=1),
        native_pydantic_model=SimpleNativePydanticModel(str_value="s", int_value=1),
    )
    model_dict = model.to_dict()

    assert model_dict == {
        "pydantic_model": {"str_value": "s", "int_value": 1},
        "native_pydantic_model": {"str_value": "s", "int_value": 1},
    }

    new_model = PydanticNestedMixedModel.from_dict(model_dict)
    assert new_model == model
