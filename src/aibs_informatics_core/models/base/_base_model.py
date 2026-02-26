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
from pathlib import Path
from typing import Protocol, Self, TypeVar, runtime_checkable

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
    def from_dict(cls: type[Self], data: JSONObject, **kwargs) -> Self: ...  # pragma: no cover

    def to_dict(self, **kwargs) -> JSONObject: ...  # pragma: no cover

    @classmethod
    def from_json(cls: type[Self], data: str, **kwargs) -> Self: ...  # pragma: no cover

    def to_json(self, **kwargs) -> str: ...  # pragma: no cover

    @classmethod
    def from_path(cls: type[Self], path: Path, **kwargs) -> Self: ...  # pragma: no cover

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
<<<<<<< HEAD
=======
            path.read_text()
>>>>>>> cec9eca (upgrading all code to python 3.10 using pyupgrade --py310-plus)
            with open(path) as f:
                return cls.from_dict(yaml.safe_load(f), **kwargs)
        else:
            return cls.from_dict(json.loads(path.read_text()), **kwargs)

    def to_path(self, path: Path, **kwargs):
        path.write_text(self.to_json(**kwargs))
