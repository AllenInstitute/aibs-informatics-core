from typing import Optional

from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.version import Version, VersionStr
from test.base import does_not_raise


@mark.parametrize(
    "input, expected, raises_error",
    [
        param("1.0.0", Version(1, 0, 0), does_not_raise()),
        param("1.0.*", Version(1, 0, None), does_not_raise()),
        param("1.0", Version(1, 0, None), does_not_raise()),
        param("1.*", Version(1, None, None), does_not_raise()),
        param("1", Version(1, None, None), does_not_raise()),
        param("v1", Version(1, None, None), does_not_raise()),
        param("v1.1", Version(1, 1, None), does_not_raise()),
        param("r1.1", None, raises(ValidationError), id="invalid prefix"),
        param("1.1.1.2.3", None, raises(ValidationError), id="invalid Too many versions"),
        param("one.two.three", None, raises(ValidationError), id="invalid non digit versions"),
    ],
)
def test_version(input: str, expected: Optional[Version], raises_error):
    with raises_error:
        version_str = VersionStr(input)

    if expected is not None:
        assert version_str.major_version == expected.major_version
        assert version_str.minor_version == expected.minor_version
        assert version_str.revision == expected.revision


@mark.parametrize(
    "this, comparison_operator, other",
    [
        param(VersionStr("1.2.3"), "==", "1.2.3"),
        param(VersionStr("1.2.3").version, "==", VersionStr("1.2.3").version),
        param(VersionStr("1.2.3"), ">", Version(1, 2, 2)),
        param(VersionStr("1.2.3"), ">=", Version(1, 2, 2)),
        param(VersionStr("1.2.3"), ">=", Version(1, 2, 3)),
        param(VersionStr("1.2.3"), "==", Version(1, 2, 3)),
        param(VersionStr("1.2.3"), "<=", Version(1, 2, 3)),
        param(VersionStr("1.2.3"), "<=", Version(1, 2, 4)),
        param(VersionStr("1.2.3"), "<", Version(1, 2, 4)),
        param(VersionStr("1.2.3"), ">", VersionStr("1.2.2")),
        param(VersionStr("1.2.3"), ">=", VersionStr("1.2.2")),
        param(VersionStr("1.2.3"), ">=", VersionStr("1.2.3")),
        param(VersionStr("1.2.3"), "==", VersionStr("1.2.3")),
        param(VersionStr("1.2.3"), "<=", VersionStr("1.2.3")),
        param(VersionStr("1.2.3"), "<=", VersionStr("1.2.4")),
        param(VersionStr("1.2.3"), "<", VersionStr("1.2.4")),
        param(VersionStr("1.0.*"), "<", VersionStr("1.0.1")),
        param(VersionStr("2.*"), ">", VersionStr("1.*")),
        param(VersionStr("2"), ">", VersionStr("1.*")),
    ],
)
def test__Version__comparison(this, other, comparison_operator):
    if comparison_operator == "==":
        assert this == other
    elif comparison_operator == "<":
        assert this < other
    elif comparison_operator == ">":
        assert this > other
    elif comparison_operator == "<=":
        assert this <= other
    elif comparison_operator == ">=":
        assert this >= other
    else:
        assert False


def test__unsupported_comparisons():
    assert not Version(1, 2, 3) == 1.2
    assert Version(1, 2, 3) is not None
    assert not VersionStr("1.2.3") == 1.2
    assert not VersionStr("1.2.3") == "1.2.a13bc"
