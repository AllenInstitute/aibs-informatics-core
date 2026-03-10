__all__ = [
    "camelcase",
    "is_prefixed",
    "is_suffixed",
    "lowercase",
    "pascalcase",
    "removeprefix",
    "removesuffix",
    "snakecase",
    "spinalcase",
    "uppercase",
]

import stringcase


def is_prefixed(value: str, prefix: str) -> bool:
    """Check whether a string starts with the given prefix.

    Args:
        value: The string to check.
        prefix: The prefix to look for.

    Returns:
        True if ``value`` starts with ``prefix``.
    """
    return value[: len(prefix)] == prefix


def is_suffixed(value: str, suffix: str) -> bool:
    """Check whether a string ends with the given suffix.

    Args:
        value: The string to check.
        suffix: The suffix to look for.

    Returns:
        True if ``value`` ends with ``suffix``.
    """
    return value[-len(suffix) :] == suffix


def removeprefix(value: str, prefix: str) -> str:
    """Remove the given prefix from the beginning of a string.

    Args:
        value: The original string.
        prefix: The prefix to remove.

    Returns:
        The string with the prefix removed, or the original string if not prefixed.
    """
    return value.removeprefix(prefix)


def removesuffix(value: str, suffix: str) -> str:
    """Remove the given suffix from the end of a string.

    Args:
        value: The original string.
        suffix: The suffix to remove.

    Returns:
        The string with the suffix removed, or the original string if not suffixed.
    """
    return value.removesuffix(suffix)


camelcase = stringcase.camelcase
spinalcase = stringcase.spinalcase
snakecase = stringcase.snakecase
pascalcase = stringcase.pascalcase


def lowercase(value: str) -> str:
    """Convert a string to lowercase.

    Args:
        value: The string to convert.

    Returns:
        The lowercased string.
    """
    return value.lower()


def uppercase(value: str) -> str:
    """Convert a string to uppercase.

    Args:
        value: The string to convert.

    Returns:
        The uppercased string.
    """
    return value.upper()
