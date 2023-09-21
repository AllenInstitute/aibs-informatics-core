import uuid
from typing import Any, ClassVar, List, Optional, Type, TypeVar, Union

import marshmallow as mm

from aibs_informatics_core.models.base import CustomStringField
from aibs_informatics_core.utils.hashing import uuid_str
from aibs_informatics_core.utils.os_operations import get_env_var

UNIQUE_ID_TYPE = TypeVar("UNIQUE_ID_TYPE", bound="UniqueID")


class UniqueID(str):
    """An augmented `str` class intended to represent a unique ID type"""

    ENV_VARS: ClassVar[List[str]] = ["UNIQUE_ID"]

    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        try:
            uuid_obj = uuid.UUID(self, version=4)
        except ValueError:
            raise mm.ValidationError(f"'{self}' is not a valid {self.__class__.__name__} (uuid4)!")
        self._uuid_obj = uuid_obj

    @classmethod
    def as_mm_field(cls, *args, **kwargs) -> mm.fields.Field:
        return CustomStringField(cls, *args, **kwargs)

    @classmethod
    def create(
        cls: Type[UNIQUE_ID_TYPE], seed: Optional[Union[int, str]] = None
    ) -> UNIQUE_ID_TYPE:
        return cls(uuid_str(str(seed)) if seed is not None else uuid.uuid4())

    def as_uuid(self) -> uuid.UUID:
        return self._uuid_obj

    @classmethod
    def from_env(cls: Type[UNIQUE_ID_TYPE]) -> UNIQUE_ID_TYPE:
        env_var = get_env_var(*cls.ENV_VARS)
        if env_var is None:
            raise ValueError(
                f"Could not find environment variable for {cls} given ENV VARS: {cls.ENV_VARS}"
            )
        return cls(env_var)
