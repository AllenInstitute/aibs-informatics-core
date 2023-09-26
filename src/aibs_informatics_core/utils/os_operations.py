__all__ = [
    "expandvars",
    "find_all_paths",
    "get_env_var",
    "set_env_var",
]

import os
import re
from pathlib import Path
from typing import List, Literal, Optional, TypeVar, Union, overload


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
