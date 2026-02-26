__all__ = [
    "DynamoDBItemKey",
    "DynamoDBItemValue",
    "DynamoDBKey",
    "DynamoDBPrimaryKeyItemValue",
]

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Union

DynamoDBPrimaryKeyItemValue = Union[
    bytes,
    str,
    int,
    Decimal,
    bool,
]

# This alias refers to the allowed types as defined in `mypy_boto3_dynamodb`
# https://youtype.github.io/boto3_stubs_docs/mypy_boto3_dynamodb/service_resource/#tableget_item-method
DynamoDBItemValue = Union[
    bytes,
    bytearray,
    str,
    int,
    Decimal,
    bool,
    set[int],
    set[Decimal],
    set[str],
    set[bytes],
    set[bytearray],
    Sequence[Any],
    Mapping[str, Any],
    None,
]
DynamoDBItemKey = str
DynamoDBKey = Mapping[DynamoDBItemKey, DynamoDBItemValue]
