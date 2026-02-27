__all__ = [
    "ModelProtocol",
    "ModelBase",
    "post_dump",
    "pre_dump",
    "pre_load",
    "validates_schema",
]

import abc
import json
import sys
from pathlib import Path
from typing import Protocol, Type, TypeVar, runtime_checkable

if sys.version_info < (3, 11):
    from typing_extensions import Self  # type: ignore[import-untyped]
else:
    from typing import Self

import yaml  # type: ignore[import-untyped]
from marshmallow import post_dump, pre_dump, pre_load, validates_schema

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
    @classmethod
    def from_dict(cls: Type[Self], data: JSONObject, **kwargs) -> Self: ...  # pragma: no cover

    def to_dict(self, **kwargs) -> JSONObject: ...  # pragma: no cover

    @classmethod
    def from_json(cls: Type[Self], data: str, **kwargs) -> Self: ...  # pragma: no cover

    def to_json(self, **kwargs) -> str: ...  # pragma: no cover

    @classmethod
    def from_path(cls: Type[Self], path: Path, **kwargs) -> Self: ...  # pragma: no cover

    def to_path(self, path: Path, **kwargs): ...  # pragma: no cover


# --------------------------------------------------------------
#                             BaseModel ABC
# --------------------------------------------------------------


class ModelBase:
    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: JSONObject, **kwargs) -> Self:
        raise NotImplementedError(
            f"Must implement this method in {cls.__name__}"
        )  # pragma: no cover

    @abc.abstractmethod
    def to_dict(self, **kwargs) -> JSONObject:
        raise NotImplementedError(
            f"Must implement this method in {self.__class__.__name__}"
        )  # pragma: no cover

    @classmethod
    def from_json(cls, data: str, **kwargs) -> Self:
        return cls.from_dict(json.loads(data), **kwargs)

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(**kwargs), indent=4)

    @classmethod
    def from_path(cls, path: Path, **kwargs) -> Self:
        if path.suffix in (".yml", ".yaml"):
            path.read_text()
            with open(path, "r") as f:
                return cls.from_dict(yaml.safe_load(f), **kwargs)
        else:
            return cls.from_dict(json.loads(path.read_text()), **kwargs)

    def to_path(self, path: Path, **kwargs):
        path.write_text(self.to_json(**kwargs))
