from aibs_informatics_core.utils.tools.string_helpers import (
    is_prefixed,
    is_suffixed,
    removeprefix,
    removesuffix,
)


def test__is_prefixed__works():
    assert is_prefixed("v1", "v")
    assert is_prefixed("v1", "v1")
    assert not is_prefixed("1v1", "v1")


def test__is_suffixed__works():
    assert not is_suffixed("v1", "v")
    assert is_suffixed("v1", "v1")
    assert is_suffixed("1v1", "v1")


def test__removeprefix__works():
    assert removeprefix("v1", "v") == "1"
    assert removeprefix("v1", "v1") == ""
    assert removeprefix("1v1", "v1") == "1v1"


def test__removesuffix__works():
    assert removesuffix("v1", "v") == "v1"
    assert removesuffix("v1", "v1") == ""
    assert removesuffix("1v1", "v1") == "1"
