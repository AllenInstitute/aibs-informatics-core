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

import re


def is_prefixed(value: str, prefix: str) -> bool:
    return value[: len(prefix)] == prefix


def is_suffixed(value: str, suffix: str) -> bool:
    return value[-len(suffix) :] == suffix


def removeprefix(value: str, prefix: str) -> str:
    return value.removeprefix(prefix)


def removesuffix(value: str, suffix: str) -> str:
    return value.removesuffix(suffix)


_CAMEL_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_WORD = re.compile(r"[^A-Za-z0-9]+")


def _split_words(value: str) -> list[str]:
    value = _CAMEL_BOUNDARY.sub(r"\1_\2", value)
    value = _NON_WORD.sub("_", value)
    return [word for word in value.strip("_").split("_") if word]


def snakecase(value: str) -> str:
    return "_".join(word.lower() for word in _split_words(value))


def spinalcase(value: str) -> str:
    return snakecase(value).replace("_", "-")


def pascalcase(value: str) -> str:
    return "".join(word.capitalize() for word in _split_words(value))


def camelcase(value: str) -> str:
    words = _split_words(value)
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def lowercase(value: str) -> str:
    return value.lower()


def uppercase(value: str) -> str:
    return value.upper()
