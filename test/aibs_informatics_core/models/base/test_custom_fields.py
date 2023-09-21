import datetime as dt
from enum import Enum
from pathlib import Path

import pytest
from marshmallow import ValidationError

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

    assert CustomStringField(CustomString).serialize("another_attr", data) == None


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

    assert uf.deserialize(None, "my_optional", data) == None
    assert uf.deserialize(data["my_int"], "my_int", data) == 123
    assert uf.deserialize(data["my_int"], "my_int", data) == 123
    with pytest.raises(ValidationError):
        uf.deserialize(data["my_bool"], "my_bool", data)


def test__UnionField__serialize():
    uf = UnionField([(str, StringField()), (int, IntegerField())], required=False, allow_none=True)

    data = dict(my_str="abc", my_int=123, my_list=[], my_optional=None)

    assert uf.serialize("my_optional", data) == None
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
    assert ef.serialize("missing", data) == None
    with pytest.raises(ValidationError):
        ef.serialize("my_str", data)
    with pytest.raises(ValidationError):
        ef.serialize("my_enum", dict(my_enum="not a valid enum"))


def test__EnumField__deserialize():
    ef = EnumField(ClassEnum, allow_none=True)

    data = dict(my_enum="foo", my_str="foo", missing=None)

    assert ef.deserialize(ClassEnum.FOO, "my_enum", data) == ClassEnum.FOO
    assert ef.deserialize("foo", "my_str", data) == ClassEnum.FOO
    assert ef.deserialize(None, "missing", data) == None
    with pytest.raises(ValidationError):
        ef.deserialize("not a valid enum", "my_enum", data)


def test__PathField__serialize_deserialize():
    pf = PathField(allow_none=True)

    assert pf.serialize("my_path", dict(my_path=Path("/tmp"))) == "/tmp"
    assert pf.serialize("my_path", dict(my_path=None)) == None
    assert pf.deserialize("/tmp", "my_path", dict(my_path="/tmp")) == Path("/tmp")
    assert pf.deserialize(None, "my_path", dict(my_path=None)) == None


def test__FrozenSetField__serialize_deserialize():
    fsf = FrozenSetField(IntegerField())
    assert fsf.serialize("my_set", dict(my_set=frozenset([2, 3, 1]))) == [1, 2, 3]
    assert fsf.deserialize([2, 1, 3], "my_set", dict(my_set=[2, 1, 3])) == frozenset([1, 2, 3])
