import pytest

from aibs_informatics_core.utils.tools.strtools import (
    condense_str,
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


def test__condense_str__returns_value_unchanged_when_it_fits():
    # Must be a no-op for values already in budget. Otherwise adopting this helper
    # anywhere would silently rename every existing resource.
    assert condense_str("short-name", max_length=24) == "short-name"
    assert condense_str("a" * 24, max_length=24) == "a" * 24


def test__condense_str__condenses_to_exactly_max_length():
    assert len(condense_str("a" * 100, max_length=24)) == 24


def test__condense_str__keeps_readable_prefix_and_hex_suffix():
    result = condense_str("scratch-volume-with-a-very-long-name", max_length=24)
    assert result.startswith("scratch-volume")
    digest = result.rpartition("-")[2]
    assert len(digest) == 8
    assert all(c in "0123456789abcdef" for c in digest)


def test__condense_str__is_deterministic():
    # Names that changed between runs would churn downstream resources (e.g. register
    # a new AWS Batch job definition revision every time).
    value = "x" * 80
    assert condense_str(value, max_length=24) == condense_str(value, max_length=24)


def test__condense_str__distinguishes_values_sharing_a_long_prefix():
    # The hash covers the whole original value, not the discarded tail, so values that
    # truncate identically still differ.
    shared = "shared-prefix-" * 5
    a = condense_str(shared + "alpha", max_length=24)
    b = condense_str(shared + "beta", max_length=24)
    assert a != b
    assert a[:15] == b[:15]


def test__condense_str__honors_custom_delimiter_and_hash_length():
    result = condense_str("y" * 60, max_length=20, delimiter="_", hash_length=4)
    assert len(result) == 20
    assert result[-5] == "_"
    assert len(result.rpartition("_")[2]) == 4


@pytest.mark.parametrize("hash_length", [0, -1])
def test__condense_str__rejects_non_positive_hash_length(hash_length):
    with pytest.raises(ValueError, match="hash_length must be positive"):
        condense_str("z" * 40, max_length=24, hash_length=hash_length)


def test__condense_str__rejects_max_length_with_no_room_for_a_prefix():
    # 8 hash chars + 1 delimiter = 9; max_length 9 leaves zero prefix. Silently
    # truncating to a bare hash would invite collisions, so this is an error.
    with pytest.raises(ValueError, match="leaves no room for a prefix"):
        condense_str("q" * 40, max_length=9)
