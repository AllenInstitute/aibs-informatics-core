import datetime as dt
from contextlib import nullcontext as does_not_raise
from enum import Enum
from pathlib import Path

import marshmallow as mm
import pytest
from marshmallow.exceptions import ValidationError

from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.base.custom_fields import (
    CustomAwareDateTime,
    CustomStringField,
    EnumField,
    FrozenSetField,
    IntegerField,
    PathField,
    StringField,
    UnionField,
)
from aibs_informatics_core.models.unique_ids import UniqueID

# ----------------------------------------------------------
#                      Custom field tests
# ----------------------------------------------------------


class CustomString(str):
    pass


def test__CustomStringField__serialize_works():
    data = dict(attr="abc", another_attr=None)
    assert CustomStringField(CustomString).serialize("attr", data) == "abc"

    with pytest.raises(ValidationError):
        CustomStringField(CustomString, strict_mode=True).serialize("attr", data)

    assert CustomStringField(CustomString).serialize("another_attr", data) is None


def test__CustomAwareDateTime__deserialize_works():
    t1 = dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc)
    t2 = dt.datetime(2022, 3, 11, 8, 23, 51, 248794)

    data = dict(t1_str=t1.isoformat(), t1_dt=t1, t2_str=t2.isoformat(), t2_dt=t2)

    assert CustomAwareDateTime(format="iso8601").deserialize(data["t1_dt"], "t1_dt", data) == t1
    assert CustomAwareDateTime(format="iso8601").deserialize(data["t1_str"], "t1_str", data) == t1

    with pytest.raises(ValidationError):
        assert CustomAwareDateTime(format="iso8601").deserialize(data["t2_dt"], "t2_dt", data)

    with pytest.raises(ValidationError):
        assert CustomAwareDateTime(format="iso8601").deserialize(data["t2_str"], "t2_str", data)


def test__UnionField__deserialize_tests():
    uf = UnionField([(str, StringField()), (int, IntegerField())], required=False, allow_none=True)

    data = dict(my_str="abc", my_int=123, my_bool=True)

    assert uf.deserialize(None, "my_optional", data) is None
    assert uf.deserialize(data["my_int"], "my_int", data) == 123
    assert uf.deserialize(data["my_int"], "my_int", data) == 123
    with pytest.raises(ValidationError):
        uf.deserialize(data["my_bool"], "my_bool", data)


def test__UnionField__serialize():
    uf = UnionField([(str, StringField()), (int, IntegerField())], required=False, allow_none=True)

    data = dict(my_str="abc", my_int=123, my_list=[], my_optional=None)

    assert uf.serialize("my_optional", data) is None
    assert uf.serialize("my_str", data) == "abc"
    assert uf.serialize("my_int", data) == 123

    with pytest.raises(ValidationError):
        uf.serialize("my_list", data)


class ClassEnum(Enum):
    FOO = "foo"
    BAR = "BAR"
    QAZ = "qazzz"


def test__EnumField__serialize():
    ef = EnumField(ClassEnum)

    data = dict(my_enum=ClassEnum.FOO, my_str="foo", missing=None)

    assert ef.serialize("my_enum", data) == "foo"
    assert ef.serialize("missing", data) is None
    with pytest.raises(ValidationError):
        ef.serialize("my_str", data)
    with pytest.raises(ValidationError):
        ef.serialize("my_enum", dict(my_enum="not a valid enum"))


def test__EnumField__deserialize():
    ef = EnumField(ClassEnum, allow_none=True)

    data = dict(my_enum="foo", my_str="foo", missing=None)

    assert ef.deserialize(ClassEnum.FOO, "my_enum", data) == ClassEnum.FOO
    assert ef.deserialize("foo", "my_str", data) == ClassEnum.FOO
    assert ef.deserialize(None, "missing", data) is None
    with pytest.raises(ValidationError):
        ef.deserialize("not a valid enum", "my_enum", data)


def test__PathField__serialize_deserialize():
    pf = PathField(allow_none=True)

    assert pf.serialize("my_path", dict(my_path=Path("/tmp"))) == "/tmp"
    assert pf.serialize("my_path", dict(my_path=None)) is None
    assert pf.deserialize("/tmp", "my_path", dict(my_path="/tmp")) == Path("/tmp")
    assert pf.deserialize(None, "my_path", dict(my_path=None)) is None


def test__FrozenSetField__serialize_deserialize():
    fsf = FrozenSetField(IntegerField())
    assert fsf.serialize("my_set", dict(my_set=frozenset([2, 3, 1]))) == [1, 2, 3]
    assert fsf.deserialize([2, 1, 3], "my_set", dict(my_set=[2, 1, 3])) == frozenset([1, 2, 3])


@pytest.mark.parametrize(
    "uid_field, input_value, raise_expectation, expected",
    [
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": UniqueID("b1c90b77-0a27-41ab-af0c-f6d99690b18e")},
            # raise_expectation
            does_not_raise(),
            # expected
            {"uid": "b1c90b77-0a27-41ab-af0c-f6d99690b18e"},
            id="Basic serialization works",
        ),
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": "im the wrong type"},
            # raise_expectation
            pytest.raises(
                ValidationError,
                match=(
                    r"'im the wrong type' \(type: <class 'str'>\) is not a "
                    r"<class '(.*).UniqueID'> type!"
                ),
            ),
            # expected
            None,
            id="Trying to serialize wrong type fails",
        ),
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": "b1c90b77-0a27-41ab-af0c-f6d99690b18e"},
            # raise_expectation
            does_not_raise(),
            # expected
            {"uid": "b1c90b77-0a27-41ab-af0c-f6d99690b18e"},
            id="Trying to serialize instance succeeds when cast as desired str class",
        ),
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": S3URI.build("bucket", "key")},
            # raise_expectation
            pytest.raises(
                ValidationError,
                match=(
                    r"'(.+)' \(type: <class '(.+)'>\) is not a " r"<class '(.*).UniqueID'> type!"
                ),
            ),
            # expected
            None,
            id="Trying to serialize mismatched UniqueID type fails",
        ),
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": UniqueID("b1c90b77-0a27-41ab-af0c-f6d99690b18e")},
            # raise_expectation
            # raise_expectation
            does_not_raise(),
            # expected
            {"uid": "b1c90b77-0a27-41ab-af0c-f6d99690b18e"},
            id="Trying to serialize subclassed UniqueID type succeeds",
        ),
    ],
)
def test_unique_id_field_serialize(uid_field, input_value, raise_expectation, expected):
    class TestSchema(mm.Schema):
        uid = uid_field

    with raise_expectation:
        obt = TestSchema().dump(input_value)

    if expected is not None:
        assert expected == obt


@pytest.mark.parametrize(
    "uid_field, input_value, raise_expectation, expected",
    [
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": "e31ed78e-f165-4bf6-9236-dc4a877c20c0"},
            # raise_expectation,
            does_not_raise(),
            # expected
            {"uid": UniqueID("e31ed78e-f165-4bf6-9236-dc4a877c20c0")},
            id="Basic deserialization works",
        ),
        pytest.param(
            # uid_field
            CustomStringField(UniqueID, required=True),
            # input_value
            {"uid": "im_not_a_valid_uuid"},
            # raise_expectation,
            pytest.raises(mm.ValidationError, match=r"(.+) is not a valid (.+) \(uuid4\)!"),
            # expected
            None,
            id="Trying to deserialize an invalid input fails",
        ),
    ],
)
def test_unique_id_field_deserialize(uid_field, input_value, raise_expectation, expected):
    class TestSchema(mm.Schema):
        uid = uid_field

    with raise_expectation:
        obt = TestSchema().load(input_value)

    if expected is not None:
        assert expected == obt


@pytest.mark.parametrize(
    "input_value, raise_expectation, expected",
    [
        pytest.param(
            # input_value
            "2022-03-11 08:23:51.248794",
            # raise_expectation
            pytest.raises(ValidationError, match="Not a valid aware datetime"),
            # expected
            None,
            id="Not timezone aware str not in iso8601",
        ),
        pytest.param(
            "2022-03-11T08:23:51.248794",
            pytest.raises(ValidationError, match="Not a valid aware datetime"),
            None,
            id="Not timezone aware str in iso8601",
        ),
        pytest.param(
            "2022-03-11 08:23:51.248794+00:00",
            does_not_raise(),
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
            id="Timezone aware str not in iso8601",
        ),
        pytest.param(
            "2022-03-11T08:23:51.248794+00:00",
            does_not_raise(),
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
            id="Timezone aware str in iso8601",
        ),
        pytest.param(
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794),
            pytest.raises(ValidationError, match="Not a valid aware datetime"),
            None,
            id="Timezone naive datetime as input",
        ),
        pytest.param(
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
            does_not_raise(),
            dt.datetime(2022, 3, 11, 8, 23, 51, 248794, dt.timezone.utc),
            id="Timezone aware datetime as input",
        ),
    ],
)
def test_custom_aware_datetime(input_value, raise_expectation, expected):
    class TestSchema(mm.Schema):
        test_input_attr = CustomAwareDateTime(format="iso8601", required=True)

    test_schema = TestSchema()

    with raise_expectation:
        res = test_schema.load({"test_input_attr": input_value})

    if expected is not None:
        assert expected == res["test_input_attr"]  # type: ignore
