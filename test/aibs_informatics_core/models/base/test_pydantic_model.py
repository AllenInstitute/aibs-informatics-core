from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional
import uuid
from aibs_informatics_test_resources import does_not_raise
from pydantic import ValidationError
import pytest
import yaml

from aibs_informatics_core.models.base._pydantic_model import PydanticBaseModel
from aibs_informatics_core.models.base._pydantic_fields import IsoDateTime


class Empty(PydanticBaseModel):
    pass


class Simple(PydanticBaseModel):
    str_value: str
    int_value: int


class SimpleChild(Simple):
    bool_value: bool


class SimpleNested(PydanticBaseModel):
    empty: Empty
    required_simple: Simple
    optional_simple: Optional[Simple] = None


class SimpleCollection(PydanticBaseModel):
    simples: List[Simple]


class Complex(PydanticBaseModel):
    uuid_value: uuid.UUID
    dt_value: IsoDateTime


class ComplexNested(PydanticBaseModel):
    required: Complex
    optional: Optional[Complex] = None


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
            Simple(str_value="str", int_value=1),
            {"str_value": "str", "int_value": 1},
            does_not_raise(),
            id=f"{Simple.__name__}",
        ),
        pytest.param(
            SimpleChild(str_value="str", int_value=1, bool_value=True),
            {"str_value": "str", "int_value": 1, "bool_value": True},
            does_not_raise(),
            id=f"{SimpleChild.__name__}",
        ),
        pytest.param(
            SimpleNested(empty=Empty(), required_simple=Simple(str_value="str", int_value=1)),
            {
                "empty": {},
                "required_simple": {"str_value": "str", "int_value": 1},
            },
            does_not_raise(),
            id=f"{SimpleNested.__name__}",
        ),
        pytest.param(
            SimpleCollection(
                simples=[
                    Simple(str_value="str1", int_value=1),
                    Simple(str_value="str2", int_value=2),
                ]
            ),
            {
                "simples": [
                    {"str_value": "str1", "int_value": 1},
                    {"str_value": "str2", "int_value": 2},
                ],
            },
            does_not_raise(),
            id=f"{SimpleCollection.__name__}",
        ),
        pytest.param(
            ComplexNested(
                required=Complex(
                    uuid_value=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                    dt_value=datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
                )
            ),
            {
                "required": {
                    "uuid_value": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                    "dt_value": "2022-03-11T08:23:51.248794+00:00",
                },
            },
            does_not_raise(),
            id=f"{ComplexNested.__name__}",
        ),
    ],
)
def test__PydanticModel__to_dict(model, expected_json, raise_exception):
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
            Simple(str_value="str", int_value=1),
            does_not_raise(),
            id=f"{Simple.__name__}",
        ),
        pytest.param(
            SimpleChild,
            {"str_value": "str", "int_value": 1, "bool_value": True},
            SimpleChild(str_value="str", int_value=1, bool_value=True),
            does_not_raise(),
            id=f"{SimpleChild.__name__}",
        ),
        pytest.param(
            SimpleNested,
            {
                "empty": {},
                "required_simple": {"str_value": "str", "int_value": 1},
                "optional_simple": None,
            },
            SimpleNested(empty=Empty(), required_simple=Simple(str_value="str", int_value=1)),
            does_not_raise(),
            id=f"{SimpleNested.__name__}",
        ),
        pytest.param(
            SimpleCollection,
            {
                "simples": [
                    {"str_value": "str1", "int_value": 1},
                    {"str_value": "str2", "int_value": 2},
                ],
            },
            SimpleCollection(
                simples=[
                    Simple(str_value="str1", int_value=1),
                    Simple(str_value="str2", int_value=2),
                ]
            ),
            does_not_raise(),
            id=f"{SimpleCollection.__name__}",
        ),
        pytest.param(
            ComplexNested,
            {
                "required": {
                    "uuid_value": "dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96",
                    "dt_value": "2022-03-11T08:23:51.248794+00:00",
                },
                "optional": None,
            },
            ComplexNested(
                required=Complex(
                    uuid_value=uuid.UUID("dfe7b672-91e0-4c2d-ac06-30dd1ac2eb96"),
                    dt_value=datetime.fromisoformat("2022-03-11T08:23:51.248794+00:00"),
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
