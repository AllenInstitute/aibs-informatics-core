__all__ = [
    "ModelProtocol",
    "ModelBase",
    "M",
]

import abc
import json
from pathlib import Path
from typing import Protocol, Self, TypeVar, runtime_checkable

import yaml  # type: ignore[import-untyped]

from aibs_informatics_core.utils.json import JSONObject

T = TypeVar("T")


DEFAULT_PARTIAL = False
DEFAULT_VALIDATE = True

M = TypeVar("M", bound="ModelBase")

# --------------------------------------------------------------
#                             ModelProtocol
# --------------------------------------------------------------


@runtime_checkable
class ModelProtocol(Protocol):
    """Runtime-checkable protocol defining the serialization/deserialization interface.

    Any class implementing this protocol must provide methods to convert
    to/from dictionaries, JSON strings, and file paths.
    """

    @classmethod
    def from_dict(cls: type[Self], data: JSONObject, **kwargs) -> Self:  # pragma: no cover
        """Create an instance from a dictionary.

        Args:
            data: Dictionary representation of the model.
            **kwargs: Additional keyword arguments for deserialization.

        Returns:
            A new instance of the model.
        """
        ...

    def to_dict(self, **kwargs) -> JSONObject:  # pragma: no cover
        """Serialize the model to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for serialization.

        Returns:
            Dictionary representation of the model.
        """
        ...

    @classmethod
    def from_json(cls: type[Self], data: str, **kwargs) -> Self:  # pragma: no cover
        """Create an instance from a JSON string.

        Args:
            data: JSON string representation of the model.
            **kwargs: Additional keyword arguments for deserialization.

        Returns:
            A new instance of the model.
        """
        ...

    def to_json(self, **kwargs) -> str:  # pragma: no cover
        """Serialize the model to a JSON string.

        Args:
            **kwargs: Additional keyword arguments for serialization.

        Returns:
            JSON string representation of the model.
        """
        ...

    @classmethod
    def from_path(cls: type[Self], path: Path, **kwargs) -> Self:  # pragma: no cover
        """Create an instance from a file path (JSON or YAML).

        Args:
            path: Path to the file to read.
            **kwargs: Additional keyword arguments for deserialization.

        Returns:
            A new instance of the model.
        """
        ...

    def to_path(self, path: Path, **kwargs):  # pragma: no cover
        """Serialize the model and write it to a file.

        Args:
            path: Path to the file to write.
            **kwargs: Additional keyword arguments for serialization.
        """
        ...


# --------------------------------------------------------------
#                             BaseModel ABC
# --------------------------------------------------------------


class ModelBase:
    """Abstract base class implementing common serialization methods.

    Provides JSON, YAML, and file I/O serialization. Subclasses must implement
    `from_dict` and `to_dict`.
    """

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: JSONObject, **kwargs) -> Self:
        """Create an instance from a dictionary.

        Args:
            data: Dictionary representation of the model.
            **kwargs: Additional keyword arguments for deserialization.

        Returns:
            A new instance of the model.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError(
            f"Must implement this method in {cls.__name__}"
        )  # pragma: no cover

    @abc.abstractmethod
    def to_dict(self, **kwargs) -> JSONObject:
        """Serialize the model to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for serialization.

        Returns:
            Dictionary representation of the model.

        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError(
            f"Must implement this method in {self.__class__.__name__}"
        )  # pragma: no cover

    @classmethod
    def from_json(cls, data: str, **kwargs) -> Self:
        """Create an instance from a JSON string.

        Args:
            data: JSON string representation of the model.
            **kwargs: Additional keyword arguments passed to `from_dict`.

        Returns:
            A new instance of the model.
        """
        return cls.from_dict(json.loads(data), **kwargs)

    def to_json(self, **kwargs) -> str:
        """Serialize the model to a JSON string.

        Args:
            **kwargs: Additional keyword arguments passed to `to_dict`.

        Returns:
            JSON string representation of the model (indented with 4 spaces).
        """
        return json.dumps(self.to_dict(**kwargs), indent=4)

    @classmethod
    def from_path(cls, path: Path, **kwargs) -> Self:
        """Create an instance from a JSON or YAML file.

        Args:
            path: Path to the file. Files with `.yml` or `.yaml` extensions
                are parsed as YAML; all others are parsed as JSON.
            **kwargs: Additional keyword arguments passed to `from_dict`.

        Returns:
            A new instance of the model.
        """
        if path.suffix in (".yml", ".yaml"):
<<<<<<< HEAD
=======
            path.read_text()
>>>>>>> cec9eca (upgrading all code to python 3.10 using pyupgrade --py310-plus)
            with open(path) as f:
                return cls.from_dict(yaml.safe_load(f), **kwargs)
        else:
            return cls.from_dict(json.loads(path.read_text()), **kwargs)

    def to_path(self, path: Path, **kwargs):
        """Serialize the model and write it to a file as JSON.

        Args:
            path: Path to the output file.
            **kwargs: Additional keyword arguments passed to `to_json`.
        """
        path.write_text(self.to_json(**kwargs))

    @classmethod
    def is_valid(cls, data: JSONObject, **kwargs) -> bool:
        """Checks whether model is valid.

        Args:
            data (JSONObject): data to validate against model
            **kwargs: additional kwargs to pass to from_dict method for validation

        Returns:
            bool: True if the model is valid, False otherwise.
        """
        try:
            cls.from_dict(data, **kwargs)
            return True
        except Exception:
            return False
