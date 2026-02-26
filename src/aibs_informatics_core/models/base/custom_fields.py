from __future__ import annotations

__all__ = [
    "BooleanField",
    "CustomAwareDateTime",
    "CustomStringField",
    "DictField",
    "EnumField",
    "FloatField",
    "FrozenSetField",
    "IntegerField",
    "ListField",
    "MappingField",
    "NestedField",
    "PathField",
    "RawField",
    "StringField",
    "TupleField",
    "UnionField",
    "UUIDField",
]

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
S = TypeVar("S", bound=str)
E = TypeVar("E")


@dataclass
class _FieldStub:
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class EnumField(_FieldStub, Generic[E]):
    pass


class PathField(_FieldStub):
    pass


class FrozenSetField(_FieldStub):
    pass


class CustomStringField(_FieldStub, Generic[S]):
    def __init__(self, str_cls: type[S], *args, strict_mode: bool = False, **kwargs):
        super().__init__(str_cls, *args, strict_mode=strict_mode, **kwargs)
        self.str_cls = str_cls
        self.strict_mode = strict_mode


class CustomAwareDateTime(_FieldStub):
    pass


class UnionField(_FieldStub):
    pass


class BooleanField(_FieldStub):
    pass


class DictField(_FieldStub):
    pass


class FloatField(_FieldStub):
    pass


class IntegerField(_FieldStub):
    pass


class MappingField(_FieldStub):
    pass


class NestedField(_FieldStub):
    pass


class ListField(_FieldStub):
    pass


class RawField(_FieldStub):
    pass


class StringField(_FieldStub):
    pass


class TupleField(_FieldStub):
    pass


class UUIDField(_FieldStub):
    pass
