import json
import uuid
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml
from aibs_informatics_test_resources import does_not_raise
from pydantic import ValidationError

from aibs_informatics_core.models.base._pydantic_fields import IsoDateTime
from aibs_informatics_core.models.base._pydantic_model import PydanticBaseModel


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
    optional_simple: Simple | None = None


class SimpleCollection(PydanticBaseModel):
    simples: list[Simple]


class Complex(PydanticBaseModel):
    uuid_value: uuid.UUID
    dt_value: IsoDateTime


class ComplexNested(PydanticBaseModel):
    required: Complex
    optional: Complex | None = None


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
                    "dt_value": "2022-03-11T08:23:51.248794Z",
                },
            },
            does_not_raise(),
            id=f"{ComplexNested.__name__}",
        ),
    ],
)
def test__PydanticBaseModel__to_dict(model, expected_json, raise_exception):
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
def test__PydanticBaseModel__from_dict(model_cls, model_json, expected_model, raise_exception):
    with raise_exception:
        actual_model = model_cls.from_dict(model_json)
    if expected_model:
        assert actual_model == expected_model


def test__PydanticBaseModel__from_path__json_file():
    model = Simple(int_value=1, str_value="s")
    model_dict = model.to_dict()
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model.json"
        path.write_text(json.dumps(model_dict))

        new_model = Simple.from_path(path)
    assert new_model == model


def test__PydanticBaseModel__from_path__yaml_file():
    model = Simple(int_value=1, str_value="s")
    model_dict = model.to_dict()
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model.yaml"
        path.write_text(yaml.safe_dump(model_dict))

        new_model = Simple.from_path(path)
    assert new_model == model


def test__PydanticBaseModel__to_path__from_path():
    with TemporaryDirectory("w") as tmpdir:
        path = Path(tmpdir) / "model"
        model = Simple(int_value=1, str_value="s")
        model.to_path(path)
        new_model = Simple.from_path(path)
    assert new_model == model


# ------------------------------------------------------------------
#                  from_json / to_json
# ------------------------------------------------------------------


def test__PydanticBaseModel__to_json():
    model = Simple(str_value="hello", int_value=42)
    result = json.loads(model.to_json())
    assert result == {"str_value": "hello", "int_value": 42}


def test__PydanticBaseModel__from_json():
    raw = json.dumps({"str_value": "hello", "int_value": 42})
    model = Simple.from_json(raw)
    assert model == Simple(str_value="hello", int_value=42)


def test__PydanticBaseModel__to_json__from_json__roundtrip():
    original = SimpleNested(
        empty=Empty(),
        required_simple=Simple(str_value="rt", int_value=7),
    )
    restored = SimpleNested.from_json(original.to_json())
    assert restored == original


# ------------------------------------------------------------------
#                  camelCase alias handling
# ------------------------------------------------------------------


def test__PydanticBaseModel__from_dict__camel_case_keys():
    """Validation alias allows camelCase input."""
    model = Simple.from_dict({"strValue": "camel", "intValue": 99})
    assert model.str_value == "camel"
    assert model.int_value == 99


def test__PydanticBaseModel__from_dict__snake_case_keys():
    """populate_by_name=True means original field names still work."""
    model = Simple.from_dict({"str_value": "snake", "int_value": 1})
    assert model.str_value == "snake"
    assert model.int_value == 1


def test__PydanticBaseModel__to_dict__by_alias():
    """Serialization with by_alias=True emits camelCase keys."""
    model = Simple(str_value="a", int_value=1)
    result = model.to_dict(by_alias=True)
    assert result == {"strValue": "a", "intValue": 1}


# ------------------------------------------------------------------
#                  extra="ignore" behaviour
# ------------------------------------------------------------------


def test__PydanticBaseModel__from_dict__ignores_extra_keys():
    model = Simple.from_dict({"str_value": "v", "int_value": 0, "unknown_key": "dropped"})
    assert model.str_value == "v"
    assert model.int_value == 0
    assert not hasattr(model, "unknown_key")


# ------------------------------------------------------------------
#                  exclude_none default
# ------------------------------------------------------------------


def test__PydanticBaseModel__to_dict__excludes_none_by_default():
    model = SimpleNested(
        empty=Empty(),
        required_simple=Simple(str_value="x", int_value=0),
        optional_simple=None,
    )
    result = model.to_dict()
    assert "optional_simple" not in result


def test__PydanticBaseModel__to_dict__includes_none_when_requested():
    model = SimpleNested(
        empty=Empty(),
        required_simple=Simple(str_value="x", int_value=0),
        optional_simple=None,
    )
    result = model.to_dict(exclude_none=False)
    assert "optional_simple" in result
    assert result["optional_simple"] is None


# ------------------------------------------------------------------
#                  as_mm_field (Marshmallow integration)
# ------------------------------------------------------------------


def test__PydanticBaseModel__as_mm_field__returns_pydantic_field():
    from aibs_informatics_core.models.base._pydantic_fields import PydanticField

    mm_field = Simple.as_mm_field()
    assert isinstance(mm_field, PydanticField)
    assert mm_field.pydantic_model_cls is Simple


def test__PydanticBaseModel__as_mm_field__deserialize():
    mm_field = Simple.as_mm_field()
    result = mm_field._deserialize({"str_value": "mm", "int_value": 5}, None, None)
    assert isinstance(result, Simple)
    assert result.str_value == "mm"
    assert result.int_value == 5


def test__PydanticBaseModel__as_mm_field__deserialize_camel_case():
    mm_field = Simple.as_mm_field()
    result = mm_field._deserialize({"strValue": "camel", "intValue": 3}, None, None)
    assert isinstance(result, Simple)
    assert result.str_value == "camel"
    assert result.int_value == 3


def test__PydanticBaseModel__as_mm_field__serialize():
    mm_field = Simple.as_mm_field()
    model = Simple(str_value="ser", int_value=10)
    result = mm_field._serialize(model, None, None)
    assert result == {"str_value": "ser", "int_value": 10}


def test__PydanticBaseModel__as_mm_field__serialize_none():
    mm_field = Simple.as_mm_field()
    result = mm_field._serialize(None, None, None)
    assert result is None


def test__PydanticBaseModel__as_mm_field__deserialize_none():
    mm_field = Simple.as_mm_field()
    result = mm_field._deserialize(None, None, None)
    assert result is None


def test__PydanticBaseModel__as_mm_field__deserialize_invalid_raises():
    import marshmallow as mm

    mm_field = Simple.as_mm_field()
    with pytest.raises(mm.ValidationError):
        mm_field._deserialize({"str_value": 1, "int_value": 1}, None, None)


def test__PydanticBaseModel__as_mm_field__serialize_wrong_type_raises():
    import marshmallow as mm

    mm_field = Simple.as_mm_field()
    with pytest.raises(mm.ValidationError):
        mm_field._serialize("not_a_model", None, None)


# ------------------------------------------------------------------
#                  filter_kwargs (unsupported kwargs silently dropped)
# ------------------------------------------------------------------


def test__PydanticBaseModel__from_dict__ignores_unsupported_kwargs():
    """Extra kwargs not accepted by model_validate are silently dropped."""
    model = Simple.from_dict(
        {"str_value": "ok", "int_value": 1},
        partial=True,  # not a valid model_validate kwarg
        infer_missing=True,  # not a valid model_validate kwarg
    )
    assert model.str_value == "ok"
    assert model.int_value == 1


def test__PydanticBaseModel__to_dict__ignores_unsupported_kwargs():
    """Extra kwargs not accepted by model_dump are silently dropped."""
    model = Simple(str_value="ok", int_value=1)
    result = model.to_dict(
        partial=True,  # not a valid model_dump kwarg
        infer_missing=True,  # not a valid model_dump kwarg
    )
    assert result == {"str_value": "ok", "int_value": 1}


def test__PydanticBaseModel__from_dict__forwards_supported_kwargs():
    """Supported kwargs like strict are still forwarded to model_validate."""
    model = Simple.from_dict(
        {"str_value": "ok", "int_value": 1},
        strict=True,
    )
    assert model.str_value == "ok"
    assert model.int_value == 1


def test__PydanticBaseModel__to_dict__forwards_supported_kwargs():
    """Supported kwargs like include/exclude are still forwarded to model_dump."""
    model = Simple(str_value="ok", int_value=1)
    result = model.to_dict(include={"str_value"})
    assert result == {"str_value": "ok"}
    assert "int_value" not in result


def test__PydanticBaseModel__to_dict__mode_and_exclude_none_defaults():
    """Verify custom defaults (mode='json', exclude_none=True) are applied."""
    model = SimpleNested(
        empty=Empty(),
        required_simple=Simple(str_value="x", int_value=0),
        optional_simple=None,
    )
    result = model.to_dict()
    # exclude_none=True by default
    assert "optional_simple" not in result

    # override exclude_none
    result_with_none = model.to_dict(exclude_none=False)
    assert "optional_simple" in result_with_none
