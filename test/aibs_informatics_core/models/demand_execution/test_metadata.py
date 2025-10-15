from typing import Any, Optional

from aibs_informatics_test_resources import does_not_raise
from pytest import mark, param, raises

from aibs_informatics_core.models.aws.sfn import ExecutionArn
from aibs_informatics_core.models.demand_execution.metadata import DemandExecutionMetadata
from aibs_informatics_core.models.status import Status


@mark.parametrize(
    "data, expected, raise_expectation",
    [
        param(
            {
                "user": "test_user",
                "arn": "arn:aws:states:us-west-2:123456789012:execution:my-execution:1234567890",
                "tags": {"key1": "value1", "key2": "value2"},
                "notify_on": {"COMPLETED": True, "FAILED": False},
                "notify_list": [],
            },
            DemandExecutionMetadata(
                user="test_user",
                arn=ExecutionArn(
                    "arn:aws:states:us-west-2:123456789012:execution:my-execution:1234567890"
                ),
                tags={"key1": "value1", "key2": "value2"},
                notify_on={Status.COMPLETED: True, Status.FAILED: False},
                notify_list=[],
            ),
            does_not_raise(),
            id="full",
        ),
        param(
            {},
            DemandExecutionMetadata(),
            does_not_raise(),
            id="empty",
        ),
        param(
            {
                "tag": "key",
            },
            DemandExecutionMetadata(
                tags={"key": "key"},
            ),
            does_not_raise(),
            id="usage of old tag field as str",
        ),
        param(
            {
                "tag": "key",
                "tags": {"key1": "value1", "key2": "value2"},
            },
            DemandExecutionMetadata(
                tags={"key": "key", "key1": "value1", "key2": "value2"},
            ),
            does_not_raise(),
            id="usage of old tag field as str and new tags field",
        ),
        param(
            {
                "tag": ["key_1", "key_2"],
                "tags": {"key1": "value1", "key2": "value2"},
            },
            DemandExecutionMetadata(
                tags={"key_1": "key_1", "key_2": "key_2", "key1": "value1", "key2": "value2"},
            ),
            does_not_raise(),
            id="usage of old tag field as list and new tags field",
        ),
        param(
            {
                "tag": ["key1", "key2"],
            },
            DemandExecutionMetadata(
                tags={"key1": "key1", "key2": "key2"},
            ),
            does_not_raise(),
            id="usage of old tag field as list",
        ),
        param(
            {
                "tag": "key1,key2",
            },
            DemandExecutionMetadata(
                tags={"key1": "key1", "key2": "key2"},
            ),
            does_not_raise(),
            id="usage of old tag field as str of comma separated key-only tags",
        ),
        param(
            {
                "tag": "key1,key2=value2",
            },
            DemandExecutionMetadata(
                tags={"key1": "key1", "key2": "value2"},
            ),
            does_not_raise(),
            id="usage of old tag field as str of comma separated key-only tags",
        ),
        param(
            {
                "tag": ["key1", "key2"],
                "tags": {"key1": "value1", "key2": "value2"},
            },
            DemandExecutionMetadata(
                tags={"key1": "value1", "key2": "value2"},
            ),
            does_not_raise(),
            id="old tags overwritten by new tags",
        ),
        param(
            {
                "tag": ValueError("Invalid tags format: 123"),
            },
            DemandExecutionMetadata(),
            does_not_raise(),
            id="invalid type old tag field ignored",
        ),
        param(
            {
                "tag": ["key1", "key2", ValueError("Invalid tags format: 123")],
            },
            DemandExecutionMetadata(),
            does_not_raise(),
            id="invalid nested types of old tag field ignored",
        ),
        param(
            {
                "tags": "tag",
            },
            None,
            raises(ValueError),
            id="invalid tags field raises error",
        ),
    ],
)
def test__DemandExecutionMetadata__from_dict(
    data: dict[str, Any], expected: Optional[DemandExecutionMetadata], raise_expectation
):
    """Test the from_dict method of DemandExecutionMetadata."""
    with raise_expectation:
        metadata = DemandExecutionMetadata.from_dict(data)
    if expected:
        assert metadata == expected


def test__DemandExecutionMetadata__tag__works():
    """Test the tag property of DemandExecutionMetadata."""
    metadata = DemandExecutionMetadata(tags={"key": "value"})
    assert metadata.tag == "key=value"
    metadata = DemandExecutionMetadata(tags={"key": "key"})
    assert metadata.tag == "key"
    metadata = DemandExecutionMetadata(tags={"flag": "flag", "key": "value"})
    assert metadata.tag == "flag,key=value"
    metadata = DemandExecutionMetadata(tags={})
    assert metadata.tag is None
