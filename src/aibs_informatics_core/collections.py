__all__ = [
    "DeepChainMap",
    "ValidatedStr",
    "Tree",
    "PostInitMixin",
    "BaseEnumMeta",
    "BaseEnum",
    "OrderedEnum",
    "StrEnum",
    "OrderedStrEnum",
]

import logging
from collections import ChainMap
from enum import Enum, EnumMeta
from functools import cached_property, total_ordering, wraps
from re import compile as regex_compile
from re import finditer as regex_finditer
from re import fullmatch as regex_fullmatch
from re import search as regex_search
from re import sub as regex_sub
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Hashable,
    List,
    Match,
    MutableMapping,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from aibs_informatics_core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DeepChainMap(ChainMap):
    """
    A recursive subclass of ChainMap
    Modified based on https://github.com/neutrinoceros/deep_chainmap solution
    """

    def __getitem__(self, key):
        submaps = [mapping for mapping in self.maps if key in mapping]
        if not submaps:
            return self.__missing__(key)
        if isinstance(submaps[0][key], MutableMapping):
            return DeepChainMap(*(submap[key] for submap in submaps))
        return super().__getitem__(key)

    def to_dict(self) -> dict:
        d: dict = {}
        for mapping in reversed(self.maps):
            self._depth_first_update(d, cast(MutableMapping, mapping))
        return d

    @classmethod
    def _depth_first_update(cls, target: MutableMapping, source: MutableMapping) -> None:
        for key, val in source.items():
            if not isinstance(val, MutableMapping):
                target[key] = val
                continue

            if key not in target:
                target[key] = dict()

            if isinstance(target[key], MutableMapping):
                cls._depth_first_update(target[key], val)


T = TypeVar("T")
S = TypeVar("S", bound="ValidatedStr")
KT = TypeVar("KT", bound=Hashable)
VT = TypeVar("VT")


class ValidatedStr(str):
    regex_pattern: ClassVar[Pattern]
    min_len: ClassVar[Optional[int]] = None
    max_len: ClassVar[Optional[int]] = None

    _regex_pattern_provided: ClassVar[bool] = False

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "regex_pattern"):
            cls.regex_pattern = regex_compile(r"(.*)")
        elif isinstance(cls.regex_pattern, str):
            cls.regex_pattern = regex_compile(cls.regex_pattern)
            cls._regex_pattern_provided = True
        else:
            cls._regex_pattern_provided = True

    def __new__(cls, value):
        obj = super().__new__(cls, value)
        obj._validate()
        return obj

    def _validate(self):
        value = self
        if self.has_regex_pattern() and not regex_fullmatch(self.regex_pattern, value) is not None:
            raise ValidationError(
                f"{value} did not satisfy {self.regex_pattern} pattern validation statement."
            )
        if (self.min_len and (len(value) < self.min_len)) or (
            self.max_len and (len(value) > self.max_len)
        ):
            raise ValidationError(
                f"{value} did not satisfy length constraints: "
                f"(min={self.min_len}, max={self.max_len})"
            )

    def get_match_groups(self) -> Sequence[Any]:
        self.validate_regex_pattern()
        # self.validate_regex_pattern() guarantees a match
        match = cast(Match[Any], regex_fullmatch(self.regex_pattern, self))
        # regex_pattern may not specify any groups in which case `match` will be None
        return match.groups()

    @classmethod
    def findall(cls: Type[S], string: str) -> List[S]:
        """Convenience method for re.findall
        Args:
            cls (Type[T]): ValidatedStr subclass
            string (str): string to find patterns within
        Raises:
            ValidationError - If no regex pattern is defined.
        Returns:
            List[T]: List of substrings matching pattern
        """
        cls.validate_regex_pattern()
        return [cls(match.group(0)) for match in regex_finditer(cls.regex_pattern, string)]

    @classmethod
    def suball(cls: Type[S], string: str, repl: Union[str, Callable[[Match], str]]) -> str:
        """Convenience method for running re.sub on string.
        If no regex pattern is defined, then return original.
        Args:
            cls (Type[T]): The ValidatedStr subclass
            s (str): String to find/replace
            repl (Union[str, Callable[[Match], str]]): replacement method
        Returns:
            str: string with replacements
        """
        if not cls.has_regex_pattern():
            logger.warning(f"{cls.__name__} has no regex pattern. No substitutions can be made.")
            return string
        return regex_sub(cls.regex_pattern, repl, string)

    @classmethod
    def is_prefixed(cls, string: str) -> bool:
        return cls.find_prefix(string) is not None

    @classmethod
    def find_prefix(cls: Type[S], string: str) -> Optional[S]:
        cls.validate_regex_pattern()
        for match in regex_finditer(cls.regex_pattern, string):
            if match.span()[0] == 0:
                return cls(match.group(0))
        return None

    @classmethod
    def is_suffixed(cls, string: str) -> bool:
        return cls.find_suffix(string) is not None

    @classmethod
    def find_suffix(cls: Type[S], string: str) -> Optional[S]:
        cls.validate_regex_pattern()
        for match in regex_finditer(cls.regex_pattern, string):
            if match.span()[1] == len(string):
                return cls(match.group(0))
        return None

    @classmethod
    def is_valid(cls, value: str) -> bool:
        if isinstance(value, cls):
            return True
        try:
            cls(value)
            return True
        except ValidationError:
            return False

    @classmethod
    def has_regex_pattern(cls) -> bool:
        return cls.regex_pattern is not None and cls._regex_pattern_provided

    @classmethod
    def validate_regex_pattern(cls, raise_error: bool = True):
        if not cls.has_regex_pattern():
            msg = f"{cls.__name__} does not define a Regex Pattern."
            if raise_error:
                raise ValidationError(msg)
            logger.warning(msg)


class Tree(dict[KT, "Tree"], Generic[KT]):
    def add_sequence(self: "Tree[KT]", *keys: KT):
        __self = self
        for key in keys:
            if key not in __self:
                __self[key] = self.__class__()
            __self = __self[key]  # type: ignore

    def to_sequences(self: "Tree[KT]") -> List[Tuple[KT, ...]]:
        sequences: List[Tuple[KT, ...]] = []
        for key in self.keys():
            sub_sequences: List[Tuple[KT, ...]] = self[key].to_sequences()  # type: ignore
            if not sub_sequences:
                sequences.append((key,))
            else:
                for sub_sequence in sub_sequences:
                    sequences.append((key, *sub_sequence))
        return sequences

    def has_sequence(self: "Tree[KT]", *keys: KT) -> bool:
        return self.get_sequence(*keys) is not None

    def get_sequence(self: "Tree[KT]", *keys: KT) -> Optional["Tree[KT]"]:
        __self = self
        for key in keys:
            if key not in __self:
                return None
            __self = __self[key]  # type: ignore
        return __self  # type: ignore


class PostInitMixin:
    def __init_subclass__(cls, add_hook: bool = False, **kwargs) -> None:
        """Adds a __post_init__ method to the subclass if it does not already have one.

        If add_hook is True, then the __init__ method is wrapped to call __post_init__ after

        Args:
            add_hook (bool, optional): add hook to init method. Defaults to True.
        """
        super().__init_subclass__(**kwargs)

        if add_hook:
            original_post_init = cls.__post_init__
            original_init = cls.__init__

            @wraps(original_post_init)
            def wrapped_post_init(self, *args, **_kwargs):
                if not hasattr(self, "__post_init_called__"):
                    original_post_init(self, *args, **_kwargs)
                    self.__post_init_called__ = True

            @wraps(original_init)
            def wrapped_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                self.__post_init__()

            cls.__init__ = wrapped_init  # type: ignore[assignment]
            cls.__post_init__ = wrapped_post_init  # type: ignore[assignment]

    def __post_init__(self, *args, **kwargs):
        """Default __post_init__ method. Safe parent __post_init__ method calls"""

        try:
            post_init = super().__post_init__  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            post_init(*args, **kwargs)


class BaseEnumMeta(EnumMeta):

    """Metaclass for BaseEnum type"""

    def __contains__(self, item):
        # Membership Test
        try:
            return super().__contains__(item)
        except TypeError:
            return item in self._value2member_map_


class BaseEnum(Enum, metaclass=BaseEnumMeta):

    """
    Enum extension class that makes string comparisons easier
    >>> class MyEnum(BaseEnum):
    >>>     BLARG = "blarg"
    >>>
    >>> assert MyEnum.BLARG == "blarg"
    """

    def __eq__(self, other):
        result = self is other
        return result or other == self.value

    @classmethod
    def values(cls) -> List[Any]:
        return [c.value for c in cls]


@total_ordering
class OrderedEnum(BaseEnum):
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.__name_order__ < other.__name_order__
        try:
            return self.__name_order__ < self.__class__(other).__name_order__
        except:
            return NotImplemented

    @cached_property
    def __name_order__(self) -> int:
        return self.__class__._member_names_.index(self.name)  # type: ignore[attr-defined]


SE = TypeVar("SE", bound="StrEnum")


class StrEnum(str, BaseEnum):
    def __new__(cls: Type[SE], value: str, *args: Any, **kwargs: Any) -> SE:
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> List[str]:
        return [cast(str, c.value) for c in cls]


@total_ordering
class OrderedStrEnum(str, OrderedEnum):
    @classmethod
    def values(cls) -> List[str]:
        return [cast(str, c.value) for c in cls]

    ## str class overrides

    def __lt__(self, __x) -> bool:
        return OrderedEnum.__lt__(self, __x)

    def __le__(self, __x) -> bool:
        return OrderedEnum.__le__(self, __x)  # type: ignore[operator]  ## attached using `total_ordering` decorator

    def __ge__(self, __x) -> bool:
        return OrderedEnum.__ge__(self, __x)  # type: ignore[operator]  ## attached using `total_ordering` decorator

    def __gt__(self, __x) -> bool:
        return OrderedEnum.__gt__(self, __x)  # type: ignore[operator]  ## attached using `total_ordering` decorator
