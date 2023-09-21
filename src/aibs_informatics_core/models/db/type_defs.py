__all__ = [
    "DynamoDBItemKey",
    "DynamoDBItemValue",
    "DynamoDBKey",
    "DynamoDBPrimaryKeyItemValue",
]

from decimal import Decimal
from typing import Any, Mapping, Sequence, Set, Union

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
    Set[int],
    Set[Decimal],
    Set[str],
    Set[bytes],
    Set[bytearray],
    Sequence[Any],
    Mapping[str, Any],
    None,
]
DynamoDBItemKey = str
DynamoDBKey = Mapping[DynamoDBItemKey, DynamoDBItemValue]
