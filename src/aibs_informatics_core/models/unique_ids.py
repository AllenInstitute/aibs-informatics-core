import uuid
from typing import ClassVar, TypeVar

from aibs_informatics_core.collections import PydanticStrMixin
from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.utils.hashing import uuid_str
from aibs_informatics_core.utils.os_operations import get_env_var

UNIQUE_ID_TYPE = TypeVar("UNIQUE_ID_TYPE", bound="UniqueID")


class UniqueID(str, PydanticStrMixin):
    """An augmented `str` class intended to represent a unique ID type"""

    ENV_VARS: ClassVar[list[str]] = ["UNIQUE_ID"]

    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        """Validate that the string is a valid UUID4.

        Raises:
            ValidationError: If the string is not a valid UUID4.
        """
        try:
            uuid_obj = uuid.UUID(self, version=4)
        except ValueError:
            raise ValidationError(f"'{self}' is not a valid {self.__class__.__name__} (uuid4)!")
        self._uuid_obj = uuid_obj

    @classmethod
    def create(cls: type[UNIQUE_ID_TYPE], seed: int | str | None = None) -> UNIQUE_ID_TYPE:
        """Create a new UniqueID, optionally seeded for deterministic generation.

        Args:
            seed: Optional seed value. If provided, generates a deterministic UUID.

        Returns:
            A new UniqueID instance.
        """
        return cls(uuid_str(str(seed)) if seed is not None else uuid.uuid4())

    def as_uuid(self) -> uuid.UUID:
        """Return the underlying UUID object."""
        return self._uuid_obj

    @classmethod
    def from_env(cls: type[UNIQUE_ID_TYPE]) -> UNIQUE_ID_TYPE:
        """Load a UniqueID from environment variables.

        Checks the environment variables listed in ``ENV_VARS``.

        Returns:
            A UniqueID loaded from the environment.

        Raises:
            ValueError: If no matching environment variable is found.
        """
        env_var = get_env_var(*cls.ENV_VARS)
        if env_var is None:
            raise ValueError(
                f"Could not find environment variable for {cls} given ENV VARS: {cls.ENV_VARS}"
            )
        return cls(env_var)
