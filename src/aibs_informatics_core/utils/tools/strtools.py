__all__ = [
    "camelcase",
    "condense_str",
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

from aibs_informatics_core.utils.hashing import sha256_hexdigest

#: Hex characters of hash appended by :func:`condense_str` when shortening. 8 hex
#: characters is 32 bits, ample for disambiguating names within a single namespace.
DEFAULT_CONDENSE_HASH_LENGTH = 8


def condense_str(
    value: str,
    max_length: int,
    delimiter: str = "-",
    hash_length: int = DEFAULT_CONDENSE_HASH_LENGTH,
) -> str:
    """Shorten a string to a maximum length while keeping it unique and readable.

    For names that must fit a downstream length limit -- generated AWS resource names
    being the motivating case -- where plain truncation would risk collisions.

    A value that already fits is returned **unchanged**. That matters: condensing has
    to be a no-op for names already within budget, or adopting this helper somewhere
    would silently rename every existing resource.

    A value that does not fit keeps as much of its readable prefix as possible and is
    suffixed with ``delimiter`` plus a hash of the **whole original value**. Hashing
    the original rather than the discarded tail means two values sharing a long common
    prefix still condense to different results.

    The result is deterministic: the same input always condenses to the same output.
    Callers depend on that -- a name that changed between runs would, for example,
    register a new AWS Batch job definition revision every time.

    Args:
        value: The string to condense.
        max_length: Maximum length of the result. Must leave room for the hash suffix
            plus at least one character of prefix.
        delimiter: Separator placed between the truncated prefix and the hash suffix.
        hash_length: Number of hex characters of hash to append.

    Returns:
        ``value`` if it already fits within ``max_length``, otherwise
        ``<prefix><delimiter><hash>``, of exactly ``max_length`` characters.

    Raises:
        ValueError: If ``hash_length`` is not positive, or if ``max_length`` is too
            small to fit the suffix plus at least one prefix character. Truncating
            without a hash would silently invite collisions, so this is an error
            rather than a quiet fallback.

    Examples:
        >>> condense_str("short-name", max_length=24)
        'short-name'
        >>> condense_str("a" * 40, max_length=24)
        'aaaaaaaaaaaaaaa-e4bcc900'
    """
    if hash_length <= 0:
        raise ValueError(f"hash_length must be positive, got {hash_length}")

    if len(value) <= max_length:
        return value

    suffix_length = len(delimiter) + hash_length
    if max_length <= suffix_length:
        raise ValueError(
            f"Cannot condense to max_length={max_length}: the {suffix_length} character "
            f"suffix (delimiter {delimiter!r} + {hash_length} hash chars) leaves no room "
            f"for a prefix. Raise max_length or lower hash_length."
        )

    prefix = value[: max_length - suffix_length]
    return f"{prefix}{delimiter}{sha256_hexdigest(value)[:hash_length]}"


def is_prefixed(value: str, prefix: str) -> bool:
    """Check whether a string starts with the given prefix.

    Args:
        value: The string to check.
        prefix: The prefix to look for.

    Returns:
        True if ``value`` starts with ``prefix``.
    """
    return value.startswith(prefix)


def is_suffixed(value: str, suffix: str) -> bool:
    """Check whether a string ends with the given suffix.

    Args:
        value: The string to check.
        suffix: The suffix to look for.

    Returns:
        True if ``value`` ends with ``suffix``.
    """
    return value.endswith(suffix)


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
