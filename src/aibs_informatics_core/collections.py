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
from collections.abc import Callable, Hashable, MutableMapping, Sequence
from enum import Enum, EnumMeta
from functools import cached_property, total_ordering, wraps
from re import Match, Pattern
from re import compile as regex_compile
from re import finditer as regex_finditer
from re import fullmatch as regex_fullmatch
from re import sub as regex_sub
from typing import (
    Any,
    ClassVar,
    Generic,
    Optional,
    TypeVar,
    cast,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import SchemaValidator
from pydantic_core.core_schema import (
    CoreSchema,
    StringSchema,
    chain_schema,
    no_info_plain_validator_function,
    str_schema,
)

from aibs_informatics_core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DeepChainMap(ChainMap):
    """
    A recursive subclass of ChainMap
    Modified based on https://github.com/neutrinoceros/deep_chainmap solution
    """

    def __getitem__(self, key):
        """Retrieve a value, recursively merging nested mappings.

        Args:
            key: The key to look up.

        Returns:
            The value associated with the key. If the value is a mapping,
            returns a merged ``DeepChainMap`` of all submaps containing that key.
        """
        submaps = [mapping for mapping in self.maps if key in mapping]
        if not submaps:
            return self.__missing__(key)
        if isinstance(submaps[0][key], MutableMapping):
            return DeepChainMap(*(submap[key] for submap in submaps))
        return super().__getitem__(key)

    def to_dict(self) -> dict:
        """Flatten all chained maps into a single dictionary.

        Performs a depth-first merge of all maps, with earlier maps taking
        precedence over later ones.

        Returns:
            A single merged dictionary.
        """
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


class Tree(dict[KT, "Tree"], Generic[KT]):
    """A recursive dictionary for building tree structures from sequences.

    Each key maps to a child ``Tree``, forming an n-ary tree. Provides methods
    to add, retrieve, and enumerate paths (sequences of keys) through the tree.
    """

    def add_sequence(self: "Tree[KT]", *keys: KT):
        """Add a path of keys to the tree, creating intermediate nodes as needed.

        Args:
            *keys: Ordered sequence of keys representing a path from root to leaf.
        """
        __self = self
        for key in keys:
            if key not in __self:
                __self[key] = self.__class__()
            __self = __self[key]  # type: ignore

    def to_sequences(self: "Tree[KT]") -> list[tuple[KT, ...]]:
        """Enumerate all root-to-leaf paths in the tree.

        Returns:
            A list of tuples, each representing a path from root to leaf.
        """
        sequences: list[tuple[KT, ...]] = []
        for key in self.keys():
            sub_sequences: list[tuple[KT, ...]] = self[key].to_sequences()  # type: ignore
            if not sub_sequences:
                sequences.append((key,))
            else:
                for sub_sequence in sub_sequences:
                    sequences.append((key, *sub_sequence))
        return sequences

    def has_sequence(self: "Tree[KT]", *keys: KT) -> bool:
        """Check whether a path of keys exists in the tree.

        Args:
            *keys: Ordered sequence of keys to look up.

        Returns:
            True if the path exists, False otherwise.
        """
        return self.get_sequence(*keys) is not None

    def get_sequence(self: "Tree[KT]", *keys: KT) -> Optional["Tree[KT]"]:
        """Retrieve the subtree at the given path.

        Args:
            *keys: Ordered sequence of keys to traverse.

        Returns:
            The subtree at the end of the path, or None if the path does not exist.
        """
        __self = self
        for key in keys:
            if key not in __self:
                return None
            __self = __self[key]  # type: ignore
        return __self  # type: ignore


class PostInitMixin:
    """Mixin that adds ``__post_init__`` hook support to classes.

    When used with ``add_hook=True`` in ``__init_subclass__``, automatically
    calls ``__post_init__`` after ``__init__`` completes. This is useful for
    adding validation or derived attribute computation after initialization.
    """

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
            def wrapped_post_init(self, *_args, **_kwargs):
                if not hasattr(self, "__post_init_called__"):
                    original_post_init(self, *_args, **_kwargs)
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


class PydanticStrMixin:
    """Mixin for Pydantic models that provides a custom CoreSchema for string validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: object, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        if not issubclass(cls, str):
            raise TypeError("PydanticStrMixin can only be used with subclasses of str")

        str_schema_kwargs: dict[str, Any] = {}
        if issubclass(cls, ValidatedStr):
            if cls.has_regex_pattern():
                str_schema_kwargs["pattern"] = cls.regex_pattern
            if cls.min_len is not None:
                str_schema_kwargs["min_length"] = cls.min_len
            if cls.max_len is not None:
                str_schema_kwargs["max_length"] = cls.max_len

        input_schema: StringSchema | CoreSchema
        if str_schema_kwargs:
            try:
                input_schema = str_schema(**str_schema_kwargs, regex_engine="rust-regex")
                # Probe the schema to catch rust-regex incompatibilities (e.g. lookaheads)
                # since str_schema() only builds a dict and defers compilation.
                SchemaValidator(input_schema)
            except TypeError:
                # regex_engine kwarg not supported (older pydantic-core)
                input_schema = str_schema(**str_schema_kwargs)
            except Exception:
                input_schema = str_schema(**str_schema_kwargs, regex_engine="python-re")
        else:
            input_schema = handler(str)

        return chain_schema(
            [
                input_schema,
                no_info_plain_validator_function(lambda x: cls(x)),
            ]
        )


class ValidatedStr(str, PostInitMixin, PydanticStrMixin):
    """A string subclass with regex-based validation.

    Subclasses should define a ``regex_pattern`` class variable to enforce
    a specific string format. Optional ``min_len`` and ``max_len`` class
    variables can constrain string length.

    Attributes:
        regex_pattern: Compiled regex pattern used for validation.
        min_len: Minimum allowed string length, or None for no limit.
        max_len: Maximum allowed string length, or None for no limit.
    """

    regex_pattern: ClassVar[Pattern]
    min_len: ClassVar[int | None] = None
    max_len: ClassVar[int | None] = None

    _regex_pattern_provided: ClassVar[bool] = False

    def __init_subclass__(cls) -> None:
        super().__init_subclass__(add_hook=True)
        if not hasattr(cls, "regex_pattern"):
            cls.regex_pattern = regex_compile(r"(.*)")
        elif isinstance(cls.regex_pattern, str):
            cls.regex_pattern = regex_compile(cls.regex_pattern)
            cls._regex_pattern_provided = True
        else:
            cls._regex_pattern_provided = True

    def __new__(cls, value, *args, **kwargs):
        value = cls._sanitize(value, *args, **kwargs)
        obj = super().__new__(cls, value)
        return obj

    def __init__(self, *args, **kwargs):
        """Placeholder for subclass to override"""
        super().__init__()

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        self._validate()

    @classmethod
    def _sanitize(cls, value: str, *args, **kwargs) -> str:
        return value

    def _validate(self):
        value = self
        if self.has_regex_pattern() and not regex_fullmatch(self.regex_pattern, value) is not None:
            raise ValidationError(
                f"{value} did not satisfy {self.regex_pattern} pattern validation statement. "
                f"type: {type(self)}"
            )
        if (self.min_len and (len(value) < self.min_len)) or (
            self.max_len and (len(value) > self.max_len)
        ):
            raise ValidationError(
                f"{value} did not satisfy length constraints: "
                f"(min={self.min_len}, max={self.max_len})"
            )

    def get_match_groups(self) -> Sequence[Any]:
        """Return the captured groups from matching the regex pattern against this string.

        Returns:
            A sequence of matched groups.

        Raises:
            ValidationError: If no regex pattern is defined.
        """
        self.validate_regex_pattern()
        # self.validate_regex_pattern() guarantees a match
        match = cast(Match[Any], regex_fullmatch(self.regex_pattern, self))
        # regex_pattern may not specify any groups in which case `match` will be None
        return match.groups()

    @classmethod
    def findall(cls: type[S], string: str) -> list[S]:
        """Convenience method for re.findall

        Args:
            cls (Type[T]): ValidatedStr subclass
            string (str): string to find patterns within

        Raises:
            ValidationError - If no regex pattern is defined.

        Returns:
            List of substrings matching pattern
        """
        cls.validate_regex_pattern()
        return [cls(match.group(0)) for match in regex_finditer(cls.regex_pattern, string)]

    @classmethod
    def suball(cls: type[S], string: str, repl: str | Callable[[Match], str]) -> str:
        """Convenience method for running re.sub on string.
        If no regex pattern is defined, then return original.
        Args:
            cls (Type[T]): The ValidatedStr subclass
            s (str): String to find/replace
            repl (Union[str, Callable[[Match], str]]): replacement method
        Returns:
            string with replacements
        """
        if not cls.has_regex_pattern():
            logger.warning(f"{cls.__name__} has no regex pattern. No substitutions can be made.")
            return string
        return regex_sub(cls.regex_pattern, repl, string)

    @classmethod
    def is_prefixed(cls, string: str) -> bool:
        """Check if the string starts with a match of the regex pattern.

        Args:
            string: The string to check.

        Returns:
            True if a match is found at the start of the string.
        """
        return cls.find_prefix(string) is not None

    @classmethod
    def find_prefix(cls: type[S], string: str) -> S | None:
        """Find the first regex match at the start of the string.

        Args:
            string: The string to search.

        Returns:
            A validated instance of the matched prefix, or None if no prefix matches.
        """
        cls.validate_regex_pattern()
        for match in regex_finditer(cls.regex_pattern, string):
            if match.span()[0] == 0:
                return cls(match.group(0))
        return None

    @classmethod
    def is_suffixed(cls, string: str) -> bool:
        """Check if the string ends with a match of the regex pattern.

        Args:
            string: The string to check.

        Returns:
            True if a match is found at the end of the string.
        """
        return cls.find_suffix(string) is not None

    @classmethod
    def find_suffix(cls: type[S], string: str) -> S | None:
        """Find the first regex match at the end of the string.

        Args:
            string: The string to search.

        Returns:
            A validated instance of the matched suffix, or None if no suffix matches.
        """
        cls.validate_regex_pattern()
        for match in regex_finditer(cls.regex_pattern, string):
            if match.span()[1] == len(string):
                return cls(match.group(0))
        return None

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a string is a valid instance of this validated string type.

        Args:
            value: The string to validate.

        Returns:
            True if the value passes validation, False otherwise.
        """
        if isinstance(value, cls):
            return True
        try:
            cls(value)
            return True
        except ValidationError:
            return False

    @classmethod
    def has_regex_pattern(cls) -> bool:
        """Check if this class has a user-defined regex pattern.

        Returns:
            True if a regex pattern was explicitly provided.
        """
        return cls.regex_pattern is not None and cls._regex_pattern_provided

    @classmethod
    def validate_regex_pattern(cls, raise_error: bool = True):
        """Validate that a regex pattern is defined for this class.

        Args:
            raise_error: If True, raise an error when no pattern is defined.
                If False, log a warning instead.

        Raises:
            ValidationError: If ``raise_error`` is True and no regex pattern is defined.
        """
        if not cls.has_regex_pattern():
            msg = f"{cls.__name__} does not define a Regex Pattern."
            if raise_error:
                raise ValidationError(msg)
            logger.warning(msg)


class BaseEnumMeta(EnumMeta):
    """Metaclass for BaseEnum type"""

    def __contains__(self, item):
        """Test membership, supporting both enum members and raw values.

        Args:
            item: The item to check for membership.

        Returns:
            True if the item is a member or matches a member value.
        """
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
        """Compare equality by identity or by value."""
        result = self is other
        return result or other == self.value

    @classmethod
    def values(cls) -> list[Any]:
        """Return a list of all member values.

        Returns:
            List of enum member values.
        """
        return [c.value for c in cls]


@total_ordering
class OrderedEnum(BaseEnum):
    """An enum that supports ordering based on member definition order."""

    def __lt__(self, other):
        """Compare ordering based on member definition order."""
        if self.__class__ is other.__class__:
            return self.__name_order__ < other.__name_order__
        try:
            return self.__name_order__ < self.__class__(other).__name_order__
        except Exception:
            return NotImplemented

    @cached_property
    def __name_order__(self) -> int:
        return self.__class__._member_names_.index(self.name)  # type: ignore[attr-defined]


SE = TypeVar("SE", bound="StrEnum")


class StrEnum(str, BaseEnum):
    """An enum whose members are also strings, allowing direct string comparison."""

    def __new__(cls: type[SE], value: str, *args: Any, **kwargs: Any) -> SE:
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return a list of all member values as strings.

        Returns:
            List of enum member values.
        """
        return [cast(str, c.value) for c in cls]


@total_ordering
class OrderedStrEnum(str, OrderedEnum):
    """A string enum that supports ordering based on member definition order."""

    @classmethod
    def values(cls) -> list[str]:
        """Return a list of all member values as strings.

        Returns:
            List of enum member values.
        """
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
