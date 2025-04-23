from aibs_informatics_core.utils.tools.strtools import (
    is_prefixed,
    is_suffixed,
    lowercase,
    removeprefix,
    removesuffix,
    uppercase,
)


def test__is_prefixed__works():
    assert is_prefixed("v1", "v")
    assert is_prefixed("v1", "v1")
    assert not is_prefixed("1v1", "v1")


def test__is_suffixed__works():
    assert not is_suffixed("v1", "v")
    assert is_suffixed("v1", "v1")
    assert is_suffixed("1v1", "v1")


def test__lowercase__works():
    assert lowercase("v1") == "v1"
    assert lowercase("V1") == "v1"


def test__uppercase__works():
    assert uppercase("v1") == "V1"
    assert uppercase("V1") == "V1"


def test__removeprefix__works():
    assert removeprefix("v1", "v") == "1"
    assert removeprefix("v1", "v1") == ""
    assert removeprefix("1v1", "v1") == "1v1"


def test__removesuffix__works():
    assert removesuffix("v1", "v") == "v1"
    assert removesuffix("v1", "v1") == ""
    assert removesuffix("1v1", "v1") == "1"
