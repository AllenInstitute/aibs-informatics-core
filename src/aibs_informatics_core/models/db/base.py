__all__ = [
    "DBModel",
    "DBKeyNameEnum",
    "DBSortKeyNameEnum",
    "DBIndexNameEnum",
    "DBIndex",
]

from dataclasses import dataclass
from typing import List, Optional, Tuple, Type, TypeVar

from aibs_informatics_core.collections import StrEnum
from aibs_informatics_core.env import EnvBase
from aibs_informatics_core.models.base import SchemaModel
from aibs_informatics_core.models.db.type_defs import DynamoDBItemValue, DynamoDBKey


# ========================== DB entry base model =========================
@dataclass
class DBModel(SchemaModel):
    """Base class that DB Entry models should all inherit from.
    Used to disambiguate from other model classes that also inherit from
    SchemaModel (like Request/Response models)"""

    pass


# =========================== Base definitions ===========================
class DBKeyNameEnum(StrEnum):
    """An Enum that describes possible Partition Keys for a DynamoDB table

    NOTE: Convention for this Enum should be that the first enum member is the
          partition key for the main table and subsequent members describe
          partition keys for Global/Local Secondary Indices (GSIs/LSIs)
    """

    pass


class DBSortKeyNameEnum(StrEnum):
    """An Enum that describes possible Sort Keys for a DynamoDB table.

    NOTE: Not all tables/GSI's/LSI's will have a sort key
    """

    pass


class DBIndexNameEnum(StrEnum):
    """An Enum that describes names for Global/Local Secondary Indices for
    a given table.

    NOTE: Not all tables will have GSIs/LSIs
    """

    @staticmethod
    def from_name_and_key(
        table_name: str, key: DBKeyNameEnum, sort_key: Optional[DBSortKeyNameEnum] = None
    ) -> str:
        """Construct an AWS DynamoDB Secondary Index name from table_name, key, and sort_key.

        NOTE: `key` and `sort_key` names will have underscores ('_') converted to hyphens ('-')
        """
        index_name = f"{table_name}-{key.value.replace('_', '-')}"
        if sort_key:
            index_name = f"{index_name}-{sort_key.value.replace('_', '-')}"
        return f"{index_name}-index"


DB_INDEX = TypeVar("DB_INDEX", bound="DBIndex")


class DBIndex(StrEnum):
    """Helper Enum class that indexes partition keys, sort keys, and possible GSIs/LSIs

    Classes inheriting from the DBIndex should:
    - Provide an implementation of the `table_name` classmethod
    - Starting with the main table enum member, define a tuple consisting of:
        1. canonical partition key value
        2. DBKeyNameEnum representing the partition key
        3. DBSortKeyNameEnum representing the sort key (or None if table/LSI/GSI lacks a sort key)
        4. DBIndexNameEnum representing the name of the LSI/GSI if it exists (or None)
           NOTE: main table is not an LSI/GSI so this item will always be None for those.
        5. Optional list of strings representing the non-key attributes for a GSI
           NOTE: this should only be used for GSIs
    """

    _value_: str
    _key_name: DBKeyNameEnum
    _sort_key_name: Optional[DBSortKeyNameEnum]
    _index_name: Optional[DBIndexNameEnum]
    _attributes: Optional[List[str]]
    _all_values: Tuple[
        str,  # _value_
        DBKeyNameEnum,  # _key_name
        Optional[DBSortKeyNameEnum],  # _sort_key_name
        Optional[DBIndexNameEnum],  # _index_name
        Optional[List[str]],  # _attributes
    ]

    def __new__(cls, *values):
        obj = str.__new__(cls, values[0])
        # first value is canonical value
        obj._value_ = values[0]
        obj._key_name = values[1]
        # cls._value2member_map_[obj._key_name] = obj
        obj._sort_key_name = values[2]
        obj._index_name = values[3]
        obj._attributes = values[4] if len(values) > 4 else None
        obj._all_values = (
            obj._value_,
            obj._key_name,
            obj._sort_key_name,
            obj._index_name,
            obj._attributes,
        )
        return obj

    @classmethod
    def table_name(cls) -> str:
        raise NotImplementedError(  # pragma: no cover
            f"Enum inheriting from DBIndex ({cls.__name__}) needs to implement "
            "the table_name classmethod!"
        )

    @property
    def supports_strongly_consistent_read(self) -> bool:
        # Only the main DynamoDB table supports strongly consistent reads
        # See: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html
        return self._index_name is None

    @property
    def key_name(self) -> str:
        return self._key_name.value

    @property
    def sort_key_name(self) -> Optional[str]:
        if self._sort_key_name is not None:
            return self._sort_key_name.value
        return None

    @property
    def index_name(self) -> Optional[str]:
        if self._index_name is not None:
            return self._index_name.value
        return None

    @property
    def non_key_attributes(self) -> Optional[List[str]]:
        return self._attributes

    def is_partial(self) -> bool:
        return self._attributes is not None

    def get_key_filter(
        self,
        partition_value: DynamoDBItemValue,
        sort_value: Optional[DynamoDBItemValue] = None,
    ) -> DynamoDBKey:
        """Create a DynamoDB key filter for primary or composite (partition + sort) keys

        For composite keys it is okay to provide only a 'partition value' without the 'sort_value'

        Args:
            partition_value (DynamoDBItemValue): Partition key value
            sort_value (Optional[DynamoDBItemValue], optional): Optional sort key value. Defaults to None.

        Returns:
            DynamoDBKey: A DynamoDBKey mapping that maps partition and sort key names to values
        """
        return self.get_primary_key(
            partition_value=partition_value, sort_value=sort_value, strict=False
        )

    def get_primary_key(
        self,
        partition_value: DynamoDBItemValue,
        sort_value: Optional[DynamoDBItemValue] = None,
        strict: bool = True,
    ) -> DynamoDBKey:
        """Create a DynamoDB primary (primary or partition + sort) key for read/write Table item operations.

        This method needs to be strict about always providing a `sort_value` if a table/GSI/LSI
        has a 'sort key' because its output is intended to be used with functions like
        Boto3 DynamoDB Table get-item
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/table/get_item.html#get-item
        where both the partition and sort components of primary key *must* be provided.

        Args:
            partition_value (DynamoDBItemValue): Partition key value
            sort_value (Optional[DynamoDBItemValue], optional): Optional sort key value. Defaults to None.
            strict (bool): Whether a non-default 'sort_value' MUST be provided if a 'sort key'
                exists. Defaults to True ('sort_value' MUST be provided if 'sort key' exists).

        Raises:
            ValueError: If 'sort key' is undefined, but a sort key value IS provided
            ValueError: If strict=True AND if 'sort key' is defined, but NO sort key value is provided

        Returns:
            DynamoDBKey: A DynamoDBKey mapping that maps partition and sort key names to values
        """
        if self.key_name is None:
            raise ValueError(f"'{self}' has no key name.")
        db_key = {self.key_name: partition_value}

        if self.sort_key_name:
            if sort_value is None and strict:
                raise ValueError(
                    f"{self} has a sort key ({self.sort_key_name}) "
                    "but sort key value is unspecified!"
                )

            if sort_value is not None:
                db_key[self.sort_key_name] = sort_value
        else:
            if sort_value is not None:
                raise ValueError(
                    f"'{self}' has no sort key, but a sort key value was given ({str(sort_value)})"
                )
        return db_key

    def get_table_name(self, env_base: EnvBase) -> str:
        return env_base.get_resource_name(self.table_name())

    def get_index_name(self, env_base: EnvBase) -> Optional[str]:
        index_name = self.index_name
        return index_name if index_name is None else env_base.prefixed(index_name)

    @classmethod
    def options(cls) -> List[str]:
        return [_.value for _ in cls]

    @classmethod
    def get_default_index(cls: Type[DB_INDEX]) -> DB_INDEX:
        indexes: List[DB_INDEX] = list(cls)
        if len(indexes) == 0:
            raise ValueError(f"{cls.__name__} has no members!")

        for index in indexes:
            # primary index is the first index in the list and does not have name
            if index.index_name is None and not index.is_partial():
                return index
        else:
            raise ValueError(f"{cls.__name__} has no primary index!")
