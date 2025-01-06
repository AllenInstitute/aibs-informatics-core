__all__ = [
    "expandvars",
    "find_all_paths",
    "get_env_var",
    "set_env_var",
    "to_env_var_dict",
    "to_env_var_list",
    "order_env_vars",
    "generate_env_file_content",
    "write_env_file",
    "EnvVarDictItemUpper",
    "EnvVarDictItemLower",
    "EnvVarTupleItem",
    "EnvVarItem",
    "EnvVarItemType",
    "EnvVarFormat",
    "EnvVarCollection",
]

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    Union,
    cast,
    overload,
)


def expandvars(path, default=None, skip_escaped=False):
    """Expand environment variables of form $var and ${var}.
    If parameter 'skip_escaped' is True, all escaped variable references
    (i.e. preceded by backslashes) are skipped.
    Unknown variables are set to 'default'. If 'default' is None,
    they are left unchanged.
    """

    def replace_var(m):
        return os.environ.get(m.group(2) or m.group(1), m.group(0) if default is None else default)

    env_var_pattern = re.compile((r"(?<!\\)" if skip_escaped else "") + r"\$(\w+|\{([^}]*)\})")
    return re.sub(env_var_pattern, replace_var, path)


def find_all_paths(
    root: Union[str, Path], include_dirs: bool = True, include_files: bool = True
) -> List[str]:
    """Find all paths below root path

    Args:
        root (str | Path): root path to start
        include_dirs (bool, optional): Whether to include directories. Defaults to True.
        include_files (bool, optional): whether to include files. Defaults to True.
    Returns:
        List[str]: list of paths found under root
    """
    paths = []
    str_root = str(root) if isinstance(root, Path) else root
    if os.path.isfile(str_root) and include_files:
        paths.append(str_root)
    for parent, dirs, files in os.walk(str_root):
        if include_dirs:
            paths.extend([os.path.join(parent, name) for name in dirs])
        if include_files:
            paths.extend([os.path.join(parent, name) for name in files])
    return paths


@overload
def get_env_var(*keys: str) -> Optional[str]:
    ...  # pragma: no cover


@overload
def get_env_var(*keys: str, default_value: Literal[None]) -> Optional[str]:
    ...  # pragma: no cover


@overload
def get_env_var(*keys: str, default_value: str) -> str:
    ...  # pragma: no cover


def get_env_var(*keys: str, default_value: Optional[str] = None) -> Optional[str]:
    """get env variable using one of keys (sorted by priority)

    Arguments:
        keys (Tuple[str]): list of env keys to check
            (sorted based on fallback priority)
        default_value: value to use if none are found. Defaults to none

    Returns:
        Optional[str]:
    """
    for key in keys:
        val = os.environ.get(key)
        if val:
            return val
    else:
        return default_value


def set_env_var(key: str, value: str):
    os.environ[key] = value


class EnvVarDictItemUpper(TypedDict):
    Key: str
    Value: str


class EnvVarDictItemLower(TypedDict):
    key: str
    value: str


EnvVarTupleItem = Tuple[str, str]


@dataclass
class EnvVarItem:
    key: str
    value: str

    @overload
    def to_dict(self, lower: Literal[False] = False) -> EnvVarDictItemUpper:
        ...

    @overload
    def to_dict(self, lower: Literal[True]) -> EnvVarDictItemLower:
        ...

    def to_dict(self, lower: bool = False) -> Union[EnvVarDictItemUpper, EnvVarDictItemLower]:
        if lower:
            return EnvVarDictItemLower(key=self.key, value=self.value)
        else:
            return EnvVarDictItemUpper(Key=self.key, Value=self.value)

    def to_tuple(self) -> EnvVarTupleItem:
        return (self.key, self.value)

    @classmethod
    def from_any(cls, value: Any) -> "EnvVarItem":
        if isinstance(value, cls):
            return value
        elif isinstance(value, tuple):
            assert len(value) == 2
            return cls(*value)
        elif isinstance(value, dict):
            return cls(**{k.lower(): v for k, v in value.items()})
        else:
            raise ValueError(f"Invalid env_var type: {type(value)}")


EnvVarItemType = Union[
    EnvVarItem,
    EnvVarTupleItem,
    EnvVarDictItemUpper,
    EnvVarDictItemLower,
]


class EnvVarFormat(Enum):
    OBJECT = "object"
    TUPLE = "tuple"
    DICT_LOWER = "dict_lower"
    DICT_UPPER = "dict_upper"


EnvVarSequence = Union[
    Sequence[EnvVarItem],
    Sequence[EnvVarTupleItem],
    Sequence[EnvVarDictItemUpper],
    Sequence[EnvVarDictItemLower],
]

EnvVarCollection = Union[
    EnvVarSequence,
    Dict[str, str],
]


def to_env_var_dict(env_vars: EnvVarCollection) -> Dict[str, str]:
    """Converts env vars to a dict

    Args:
        env_vars (Tuple[str, str] | Dict[str, str]): env vars to convert

    Returns:
        Dict[str, str]: dict of env vars
    """
    if isinstance(env_vars, dict):
        return env_vars

    env_var_dict = {}
    env_var_items = [EnvVarItem.from_any(env_var) for env_var in env_vars]
    for env_var_item in env_var_items:
        env_var_dict[env_var_item.key] = env_var_item.value
    return env_var_dict


@overload
def to_env_var_list(env_vars: EnvVarCollection) -> List[EnvVarTupleItem]:
    ...


@overload
def to_env_var_list(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.TUPLE]
) -> List[EnvVarTupleItem]:
    ...


@overload
def to_env_var_list(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.OBJECT]
) -> List[EnvVarItem]:
    ...


@overload
def to_env_var_list(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.DICT_LOWER]
) -> List[EnvVarDictItemLower]:
    ...


@overload
def to_env_var_list(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.DICT_UPPER]
) -> List[EnvVarDictItemUpper]:
    ...


def to_env_var_list(
    env_vars: EnvVarCollection, env_var_format: EnvVarFormat = EnvVarFormat.TUPLE
) -> EnvVarSequence:
    if isinstance(env_vars, dict):
        env_var_list = [EnvVarItem(key, value) for key, value in env_vars.items()]
    else:
        env_var_list = [EnvVarItem.from_any(env_var) for env_var in env_vars]

    if env_var_format == EnvVarFormat.OBJECT:
        return env_var_list
    elif env_var_format == EnvVarFormat.TUPLE:
        env_var_tuple_list = [_.to_tuple() for _ in env_var_list]
        return env_var_tuple_list
    elif env_var_format == EnvVarFormat.DICT_LOWER:
        env_var_dict_list = [_.to_dict(lower=True) for _ in env_var_list]
        return env_var_dict_list
    elif env_var_format == EnvVarFormat.DICT_UPPER:
        env_var_dict_list = [_.to_dict(lower=False) for _ in env_var_list]
        return env_var_dict_list
    else:
        raise ValueError(f"Invalid env_var_format: {env_var_format}")


@overload
def order_env_vars(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.OBJECT]
) -> List[EnvVarItem]:
    ...


@overload
def order_env_vars(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.TUPLE]
) -> List[EnvVarTupleItem]:
    ...


@overload
def order_env_vars(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.DICT_LOWER]
) -> List[EnvVarDictItemLower]:
    ...


@overload
def order_env_vars(
    env_vars: EnvVarCollection, env_var_format: Literal[EnvVarFormat.DICT_UPPER]
) -> List[EnvVarDictItemUpper]:
    ...


def order_env_vars(
    env_vars: EnvVarCollection, env_var_format: EnvVarFormat = EnvVarFormat.TUPLE
) -> EnvVarCollection:
    """Resolve the order of environment variables based on their dependencies.

    This function performs a topological sort on the environment variables,
    ordering them based on the dependencies found in their values. If a circular
    dependency is detected, a ValueError will be raised.

    Arguments:
        environment (Dict[str, str]): A dictionary where keys are environment variable names
            and values are their corresponding values. Dependencies are represented as
            ${var_name} or $var_name in the values.

    Returns:
        List[Tuple[str, str]]: A list of tuples, where each tuple is a pair of
            environment variable name and its value, ordered based on their dependencies.

    Raises:
        ValueError: If a circular dependency is detected among the environment variables.
    """
    # Create a list of environment keys
    env_var_dict = to_env_var_dict(env_vars)
    env_keys = list(env_var_dict.keys())

    # Initialize dependency maps
    env_key_deps: Dict[str, Set[str]] = {k: set() for k in env_keys}
    env_key_deps_rev: Dict[str, Set[str]] = {k: set() for k in env_keys}

    # Populate dependency maps
    for k, v in env_var_dict.items():
        for match in cast(List[Tuple[str, str]], re.findall(r"(?:\$\{([^\}]+)\}|\$([\w]+))", v)):
            if (value := match[0] or match[1]) in env_keys:
                # Add dependencies
                env_key_deps[k].add(value)
                env_key_deps_rev[value].add(k)

    # Sort environment keys based on the number of dependencies
    unordered_env_keys = sorted(env_keys, key=lambda k: len(env_key_deps[k]), reverse=False)

    # Initialize the list of ordered environment key-value pairs
    ordered_env_key_pairs: List[EnvVarItem] = []

    # Order environment keys
    while unordered_env_keys:
        for i, k in enumerate(unordered_env_keys):
            # If a key has no dependencies, add it to the ordered list
            if not env_key_deps[k]:
                ordered_env_key_pairs.append(EnvVarItem(k, env_var_dict[k]))
                unordered_env_keys.pop(i)

                # Update dependency maps
                for rev_k in env_key_deps_rev.pop(k, set()):
                    env_key_deps[rev_k].discard(k)
                break
        else:
            # If a circular dependency is detected, raise an error
            raise ValueError("Circular dependency detected in environment variables")
    return to_env_var_list(ordered_env_key_pairs, env_var_format=env_var_format)  # type: ignore[call-overload]  # dynamic env var format doesnt work with mypy


def generate_env_file_content(env_vars: EnvVarCollection) -> str:
    """Generate the content of an environment file.

    Example:
        Given environment variables:
            - X = "${Y}/A"
            - Y = "${Z}/B"
            - Z = "C"
        Output:
            export Z=C
            export Y=${Z}/B
            export X=${Y}/A

    Args:
        env_vars (EnvVarCollection): A collection of environment variables.

    Returns:
        str: The content of the environment file.
    """
    return "\n".join(
        [
            f'export {k}="{v}"'
            # sort the remaining environment variables to proper order
            for k, v in order_env_vars(env_vars, env_var_format=EnvVarFormat.TUPLE)
        ]
    )


def write_env_file(env_vars: EnvVarCollection, path: Union[str, Path]):
    """Write environment variables to a file.

    Args:
        env_vars (EnvVarCollection): A collection of environment variables.
        path (Union[str, Path]): The path of the environment file.
    """
    path = Path(path)
    path.write_text(generate_env_file_content(env_vars))


@contextmanager
def env_var_overrides(*env_vars: EnvVarItemType):
    """Temporarily override environment variables"""
    original_env_vars = {}
    env_var_dict = to_env_var_dict(env_vars)  # type: ignore[arg-type]
    for key, value in env_var_dict.items():
        original_env_vars[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for k, v in original_env_vars.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = v
