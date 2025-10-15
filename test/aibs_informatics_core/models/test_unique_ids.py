import os
import uuid

import marshmallow as mm
import pytest
from aibs_informatics_test_resources import reset_environ_after_test

from aibs_informatics_core.models.unique_ids import UniqueID
from test.base import does_not_raise


@pytest.mark.parametrize(
    "input_value, expected, expected_as_uuid, raise_expectation",
    [
        pytest.param(
            # input_value
            "e31ed78e-f165-4bf6-9236-dc4a877c20c0",
            # expected
            "e31ed78e-f165-4bf6-9236-dc4a877c20c0",
            # expected_as_uuid
            uuid.UUID("e31ed78e-f165-4bf6-9236-dc4a877c20c0", version=4),
            # raise_expectation
            does_not_raise(),
            id="Test uuid4 (in str form) as instantiation input",
        ),
        pytest.param(
            # input_value
            uuid.UUID("e31ed78e-f165-4bf6-9236-dc4a877c20c0", version=4),
            # expected
            "e31ed78e-f165-4bf6-9236-dc4a877c20c0",
            # expected_as_uuid
            uuid.UUID("e31ed78e-f165-4bf6-9236-dc4a877c20c0", version=4),
            # raise_expectation
            does_not_raise(),
            id="Test uuid4 (in uuid.UUID form) as instantiation input",
        ),
        pytest.param(
            # input_value
            "im_not_a_valid_uuid4",
            # expected
            None,
            # expected_as_uuid
            None,
            # raise_expectation
            pytest.raises(mm.ValidationError, match=r"(.+) is not a valid (.+) \(uuid4\)!"),
            id="Test invalid uuid4 as instantiation input",
        ),
    ],
)
def test_uniqueid_instantiation(input_value, expected, expected_as_uuid, raise_expectation):
    with raise_expectation:
        obt = UniqueID(input_value)

    if expected is not None:
        assert expected == obt

    if expected_as_uuid is not None:
        assert expected_as_uuid == obt.as_uuid()


def test_uniqueid_create():
    obt = UniqueID.create()

    assert isinstance(obt.as_uuid(), uuid.UUID)
    assert isinstance(uuid.UUID(obt, version=4), uuid.UUID)


@reset_environ_after_test
def test__UniqueID__from_env__works():
    for var in UniqueID.ENV_VARS:
        os.unsetenv(var)
    with pytest.raises(Exception):
        UniqueID.from_env()

    uuid_str = "e31ed78e-f165-4bf6-9236-dc4a877c20c0"
    os.environ[UniqueID.ENV_VARS[0]] = uuid_str

    obt = UniqueID.from_env()

    assert uuid_str == obt
    assert uuid.UUID(uuid_str, version=4) == obt.as_uuid()


def test__UniqueID__as_mm_field():
    field = UniqueID.as_mm_field()
    uuid_str = "e31ed78e-f165-4bf6-9236-dc4a877c20c0"
    uuid_obj = UniqueID(uuid_str)
    assert field.deserialize(uuid_str) == uuid_obj
