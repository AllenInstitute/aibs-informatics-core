from typing import Optional

from pytest import mark, param, raises
from test.base import does_not_raise

from aibs_informatics_core.env import EnvBase, EnvType
from aibs_informatics_core.models.db import (
    DBIndex,
    DBIndexNameEnum,
    DBKeyNameEnum,
    DBSortKeyNameEnum,
    DynamoDBItemValue,
    DynamoDBKey,
)


class MockDBKey(DBKeyNameEnum):
    KEY_A = "key_a"
    KEY_B = "key_b"
    KEY_C = "key_c"


class MockDBSortKey(DBSortKeyNameEnum):
    SORT_KEY_A = "sort_key_a"
    SORT_KEY_B = "sort_key_b"


class MockDBIndexName(DBIndexNameEnum):
    GSI_X = "gsi-x-name"
    GSI_Y = "gsi-y-name"


class MockDBIndex(DBIndex):
    MAIN_TABLE = ("key_a", MockDBKey.KEY_A, None, None)
    GSI_X = ("key_b", MockDBKey.KEY_B, MockDBSortKey.SORT_KEY_A, MockDBIndexName.GSI_X)
    GSI_Y = ("key_c", MockDBKey.KEY_C, MockDBSortKey.SORT_KEY_B, MockDBIndexName.GSI_Y)

    @classmethod
    def table_name(cls) -> str:
        return "mock_table"


def test_dbindex():
    """Test properties of the DBIndex"""

    assert MockDBIndex.table_name() == "mock_table"
    assert EnvType.values() == ["dev", "test", "prod"]
    assert MockDBIndex.values() == ["key_a", "key_b", "key_c"]

    assert MockDBIndex.MAIN_TABLE.key_name == "key_a"
    assert MockDBIndex.MAIN_TABLE.sort_key_name is None
    assert MockDBIndex.MAIN_TABLE.index_name is None

    assert MockDBIndex.GSI_X.key_name == "key_b"
    assert MockDBIndex.GSI_X.sort_key_name == "sort_key_a"
    assert MockDBIndex.GSI_X.index_name == "gsi-x-name"

    assert MockDBIndex.GSI_Y.key_name == "key_c"
    assert MockDBIndex.GSI_Y.sort_key_name == "sort_key_b"
    assert MockDBIndex.GSI_Y.index_name == "gsi-y-name"

    assert MockDBIndex.MAIN_TABLE.supports_strongly_consistent_read is True
    assert MockDBIndex.GSI_X.supports_strongly_consistent_read is False
    assert MockDBIndex.GSI_Y.supports_strongly_consistent_read is False


def test__DBIndex__get_sort_key_name__works():
    # Test default behavior (raise_if_none=False)
    assert MockDBIndex.GSI_X.get_sort_key_name() == "sort_key_a"
    assert MockDBIndex.MAIN_TABLE.get_sort_key_name() is None
    # Test raise_if_none=False
    assert MockDBIndex.GSI_X.get_sort_key_name(raise_if_none=False) == "sort_key_a"
    assert MockDBIndex.MAIN_TABLE.get_sort_key_name(raise_if_none=False) is None
    # Test raise_if_none=True
    assert MockDBIndex.GSI_X.get_sort_key_name(raise_if_none=True) == "sort_key_a"
    with raises(ValueError):
        MockDBIndex.MAIN_TABLE.get_sort_key_name(raise_if_none=True)


@mark.parametrize(
    "db_index, partition_value, sort_value, strict, expected, raises_error",
    [
        param(
            MockDBIndex.MAIN_TABLE,
            "primary_key",
            None,
            True,
            {"key_a": "primary_key"},
            does_not_raise(),
            id="Simple, no sort key - strict",
        ),
        param(
            MockDBIndex.GSI_X,
            "primary_key",
            "sort_key",
            True,
            {"key_b": "primary_key", "sort_key_a": "sort_key"},
            does_not_raise(),
            id="Simple, with sort key - strict",
        ),
        param(
            MockDBIndex.GSI_X,
            "primary_key",
            None,
            True,
            None,
            raises(ValueError),
            id="Sort key defined but sort key value NOT provided - strict",
        ),
        param(
            MockDBIndex.MAIN_TABLE,
            "primary_key",
            "sort_key",
            True,
            None,
            raises(ValueError),
            id="Invalid, no sort key but sort key value provided - strict",
        ),
        param(
            MockDBIndex.GSI_X,
            "primary_key",
            None,
            False,
            {"key_b": "primary_key"},
            does_not_raise(),
            id="Sort key defined but sort key value NOT provided - NOT strict",
        ),
    ],
)
def test__DBIndex__get_primary_key(
    db_index: DBIndex,
    partition_value: DynamoDBItemValue,
    sort_value: Optional[DynamoDBItemValue],
    strict: bool,
    expected: DynamoDBKey,
    raises_error,
):
    with raises_error:
        actual = db_index.get_primary_key(
            partition_value=partition_value, sort_value=sort_value, strict=strict
        )
    if expected is not None:
        assert actual == expected


def test__DBIndex__get_default_index__works():
    assert MockDBIndex.get_default_index() == MockDBIndex.MAIN_TABLE


def test__DBIndex__get_index_name__works():
    assert MockDBIndex.GSI_X.get_index_name(EnvBase("prod")) == "prod-gsi-x-name"


def test__DBIndex__get_default_index__fails_for_no_members():
    class InvalidIndex(DBIndex):
        @classmethod
        def table_name(cls) -> str:
            return "mock_table"

    with raises(ValueError):
        InvalidIndex.get_default_index()


def test__DBIndex__get_default_index__fails_for_no_primary():
    class InvalidIndex(DBIndex):
        MAIN_TABLE = ("key_a", MockDBKey.KEY_A, None, MockDBIndexName.GSI_X)
        GSI_X = ("key_b", MockDBKey.KEY_B, MockDBSortKey.SORT_KEY_A, MockDBIndexName.GSI_X)
        GSI_Y = ("key_c", MockDBKey.KEY_C, MockDBSortKey.SORT_KEY_B, MockDBIndexName.GSI_Y)

        @classmethod
        def table_name(cls) -> str:
            return "mock_table"

    with raises(ValueError):
        InvalidIndex.get_default_index()


def test__DBIndexNameEnum__from_name_and_key__works():
    assert (
        MockDBIndexName.from_name_and_key("mock_table", MockDBKey.KEY_A, MockDBSortKey.SORT_KEY_A)
        == "mock_table-key-a-sort-key-a-index"
    )


def test__DBIndex__attributes__works():
    class AnotherDBIndex(DBIndex):
        MAIN_TABLE = ("key_a", MockDBKey.KEY_A, None, None)
        GSI_X = (
            "key_b",
            MockDBKey.KEY_B,
            MockDBSortKey.SORT_KEY_A,
            MockDBIndexName.GSI_X,
            ["key_a", "key_b"],
        )

        @classmethod
        def table_name(cls) -> str:
            return "mock_table"

    assert AnotherDBIndex.GSI_X.non_key_attributes == ["key_a", "key_b"]
