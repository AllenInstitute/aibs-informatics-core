__all__ = [
    "StringifiedResolvable",
    "StringifiedDownloadable",
    "StringifiedUploadable",
    "ResolvableBase",
    "ResolvableAction",
    "Resolvable",
    "S3Resolvable",
    "Uploadable",
    "get_resolvable_from_value",
]

import re
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, Generic, Optional, Pattern, Sequence, Type, TypeVar, Union

import marshmallow as mm

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.base import SchemaModel, custom_field
from aibs_informatics_core.utils.hashing import sha256_hexdigest

ACTION_PATTERN = " @ "
URI_PATTERN = r"(?:\w+:)?(?:\/?\/?)[^\s]+"

PATH_PATTERN = r"(?:\/)?(?:[^\0]+\/?)*"
REMOTE_PATTERN = r"[^\s]*"
LOCAL_PATTERN = r"(?:\/)?(?:[^/\0]+\/?)*"

T = TypeVar("T", bound=str)
STRINGIFIED_RESOLVABLE = TypeVar("STRINGIFIED_RESOLVABLE", bound="StringifiedResolvable")
RESOLVABLE = TypeVar("RESOLVABLE", bound="ResolvableBase")


class StringifiedResolvable(ValidatedStr):
    """Stringified representation of a Resolvable object.

    Resolvables have two components:
        source:
        destination:

    Examples:
        "s3://bucket/key"               ->    source:  "s3://bucket/key"
                                              destination: "tmp{SHA256HEX}"
        "s3://bucket/key@version"       ->    source:  "s3://bucket/key@version"
                                              destination: "tmp{SHA256HEX}"
        "s3://bucket/key @ /tmp/xxx"    ->    source:  "s3://bucket/key"
                                              destination: "/tmp/xxx"
        "@ /tmp/xxx @ s3://bucket/key"    ->    source: "/tmp/xxx"
                                              destination:  "s3://bucket/key"
    """

    regex_pattern: ClassVar[Pattern] = re.compile(
        rf"(?:({URI_PATTERN})(?:{ACTION_PATTERN})({URI_PATTERN}))|({URI_PATTERN})"
    )

    @property
    def source(self) -> str:
        return self.get_match_groups()[0] or self.get_match_groups()[-1]

    @property
    def destination(self) -> Optional[str]:
        return self.get_match_groups()[1]

    @property
    @abstractmethod
    def local(self) -> Optional[str]:
        raise NotImplementedError("please implement")

    @property
    @abstractmethod
    def remote(self) -> Optional[str]:
        raise NotImplementedError("please implement")

    @classmethod
    def from_components(
        cls: Type[STRINGIFIED_RESOLVABLE], source: str, destination: Optional[str]
    ) -> STRINGIFIED_RESOLVABLE:
        if destination:
            return cls(f"{source}{ACTION_PATTERN}{destination}")
        return cls(source)


class StringifiedDownloadable(StringifiedResolvable):
    @property
    def local(self) -> str:
        return self.destination or f"tmp{sha256_hexdigest(self.remote)[:8]}"

    @property
    def remote(self) -> str:
        return self.source


class StringifiedUploadable(StringifiedResolvable):
    @property
    def local(self) -> str:
        return self.source

    @property
    def remote(self) -> Optional[str]:
        return self.destination


class ResolvableAction(str, Enum):
    LOCALIZE = "LOCALIZE"
    DELOCALIZE = "DELOCALIZE"


# TODO: rename to rename resolvable subclasses to uploadable
#       Also add action and maybe a type field (s3, gfs, etc.)
@dataclass  # type: ignore[misc] # mypy #5374
class ResolvableBase(SchemaModel, Generic[T]):
    local: str = custom_field()
    remote: T = custom_field()

    @classmethod
    def get_action(cls) -> ResolvableAction:
        return ResolvableAction.LOCALIZE

    @classmethod
    def get_resolvable_type(cls: Type[RESOLVABLE]) -> Type[T]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore[attr-defined]

    @classmethod
    def from_any(
        cls: Type[RESOLVABLE],
        value: Any,
        default_local: Optional[str] = None,
        default_remote: Optional[T] = None,
    ) -> RESOLVABLE:
        if isinstance(value, cls):
            return value
        elif isinstance(value, dict):
            obj = cls.from_dict(value, partial=True)
            if obj.local is None or cls.is_missing(obj.local):
                if default_local is None:
                    raise ValueError(f"Local is None for {value}. No default provided")
                obj.local = default_local
            obj.remote = obj.remote or default_remote
            obj.to_dict(validate=True)
            return obj
        elif isinstance(value, str):
            return cls.from_str(value, default_local=default_local, default_remote=default_remote)
        else:
            raise ValueError(f"Value {value} is not a dict or str. Cannot create {cls}")

    @classmethod
    def from_str(
        cls: Type[RESOLVABLE],
        value: str,
        default_local: Optional[str] = None,
        default_remote: Optional[T] = None,
    ) -> RESOLVABLE:
        str_resolvable_cls = (
            StringifiedUploadable
            if cls.get_action() == ResolvableAction.DELOCALIZE
            else StringifiedDownloadable
        )

        stringified_resolvable = str_resolvable_cls(value)

        local = stringified_resolvable.local or default_local
        assert local is not None, f"Local is None for {value}"
        if stringified_resolvable.remote:
            remote = cls.get_resolvable_type()(stringified_resolvable.remote)
        else:
            remote = default_remote
        return cls(local=local, remote=remote)

    def to_str(self) -> Union[StringifiedDownloadable, StringifiedUploadable]:
        if self.get_action() == ResolvableAction.LOCALIZE:
            return StringifiedDownloadable.from_components(
                source=self.remote, destination=self.local
            )
        else:
            return StringifiedUploadable.from_components(
                source=self.local, destination=self.remote
            )

    @classmethod
    @mm.post_dump
    def _post_dump__inject_action(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        data["action"] = cls.get_action()
        return data

    @classmethod
    @mm.pre_load
    def _pre_load__pop_action(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if "action" in data:
            assert data["action"] == cls.get_action()
            del data["action"]
        return data


R = TypeVar("R", bound=ResolvableBase)


def get_resolvable_from_value(value: Any, resolvable_classes: Sequence[Type[R]]) -> R:
    """Construct resolvable object from string or dict

    If a resolvable object is provided, it returned immediately.

    Args:
        value (Any): string or dictionary. Raises error otherwise
        resolvable_classes (Sequence[Type[R]]): sequence of resolvable classes.
            They are evaluated in the order they are provided.

    Raises:
        ValueError: The input is not a valid type.
        mm.ValidationError: No resolvable object could be constructed from input

    Returns:
        R: resolvable object
    """
    if any([isinstance(value, _) for _ in resolvable_classes]):
        return value

    if not isinstance(value, (str, dict)):
        raise ValueError(
            f"Value {value} is not a dict or str. Cannot create any of these: {resolvable_classes}"
        )

    errors: Dict[str, Exception] = {}
    for resolvable_class in resolvable_classes:
        try:
            return resolvable_class.from_any(value)
        except (mm.ValidationError, ValidationError, ValueError) as e:
            errors[resolvable_class.__name__] = e
    else:
        raise mm.ValidationError(
            {**{"ALL": f"Could not create any {resolvable_classes} from {value}"}, **errors}, "n/a"
        )


@dataclass
class Resolvable(ResolvableBase[str]):
    remote: str = custom_field()


@dataclass
class S3Resolvable(ResolvableBase[S3URI]):
    remote: S3URI = custom_field(mm_field=S3URI.as_mm_field())


@dataclass
class Uploadable(Resolvable):
    @classmethod
    def get_action(cls) -> ResolvableAction:
        return ResolvableAction.DELOCALIZE
