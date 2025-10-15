from typing import Any, Optional, Tuple, Type, Union

import marshmallow as mm
from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution.resolvables import (
    R,
    Resolvable,
    S3Resolvable,
    StringifiedDownloadable,
    StringifiedResolvable,
    StringifiedUploadable,
    Uploadable,
    get_resolvable_from_value,
)
from test.base import does_not_raise


@mark.parametrize(
    "value, expected, raises_error",
    [
        param(
            "./local_path",
            ("./local_path", None),
            does_not_raise(),
            id="source, no destination",
        ),
        param(
            "./local_path @ s3://bucket/key@something",
            ("./local_path", "s3://bucket/key@something"),
            does_not_raise(),
            id="with local source, and s3 destination",
        ),
        param(
            "s3://bucket/key@something @ ./local_path",
            ("s3://bucket/key@something", "./local_path"),
            does_not_raise(),
            id="with s3 source, local destination",
        ),
        param(
            "s3://bucket/key@something @ /tmp/somefile",
            ("s3://bucket/key@something", "/tmp/somefile"),
            does_not_raise(),
            id="string embedded with s3 remote / absolute local file",
        ),
        param(
            "s3://bucket/key@something @ /tmp/somedir/",
            ("s3://bucket/key@something", "/tmp/somedir/"),
            does_not_raise(),
            id="string embedded with s3 remote / absolute local dir",
        ),
        param(
            "s3://bucket/key something @ ./local_path",
            None,
            raises(ValidationError),
            id="string with invalid spaces",
        ),
    ],
)
def test__StringifiedResolvable__parses_source_and_destination(
    value: str,
    expected: Optional[Tuple[str, str]],
    raises_error,
):
    with raises_error:
        actual = StringifiedResolvable(value)
    if expected is not None:
        assert (actual.source, actual.destination) == expected


@mark.parametrize(
    "value, cls, expected, raises_error",
    [
        param(
            "./local_path",
            StringifiedUploadable,
            ("./local_path", None),
            does_not_raise(),
            id="StringifiedUploadable with no destination",
        ),
        param(
            "gfs://4082e025bc2d7cb020b40b5fcefc62b86f0fe62c",
            StringifiedDownloadable,
            ("tmpd11f06e0", "gfs://4082e025bc2d7cb020b40b5fcefc62b86f0fe62c"),
            does_not_raise(),
            id="StringifiedDownloadable with gfs source, randomized destination",
        ),
        param(
            "gfs://4082e025bc2d7cb020b40b5fcefc62b86f0fe62c @ ./local_path",
            StringifiedDownloadable,
            ("./local_path", "gfs://4082e025bc2d7cb020b40b5fcefc62b86f0fe62c"),
            does_not_raise(),
            id="StringifiedDownloadable with gfs source, and local destination",
        ),
        param(
            "s3://bucket/key@something @ ./local_path",
            StringifiedDownloadable,
            ("./local_path", "s3://bucket/key@something"),
            does_not_raise(),
            id="StringifiedDownloadable with s3 source, local destination",
        ),
        param(
            "/tmp/path @ s3://bucket/key@something",
            StringifiedUploadable,
            ("/tmp/path", "s3://bucket/key@something"),
            does_not_raise(),
            id="StringifiedUploadable with s3 source, local destination",
        ),
    ],
)
def test__StringifiedResolvable__parses_local_and_remote(
    value: str,
    cls: Union[StringifiedDownloadable, StringifiedUploadable],
    expected: Optional[Tuple[str, str]],
    raises_error,
):
    with raises_error:
        actual = cls(value)
    if expected is not None:
        assert (actual.local, actual.remote) == expected


@mark.parametrize(
    "value, resolvable_classes, expected, raises_error",
    [
        param(
            "gs://bucket/key",
            [S3Resolvable, Resolvable],
            Resolvable("tmpdb345ebe", "gs://bucket/key"),
            does_not_raise(),
            id="gfs path string, parsed as second resolvable class",
        ),
        param(
            "s3://bucket/key",
            [S3Resolvable, Resolvable],
            S3Resolvable("tmp558ca153", S3URI("s3://bucket/key")),
            does_not_raise(),
            id="s3 path string, parsed first resolvable class",
        ),
        param(
            "s3://bucket/key",
            [Resolvable, S3Resolvable],
            Resolvable("tmp558ca153", "s3://bucket/key"),
            does_not_raise(),
            id="s3 path string, parsed by generic resolvable class",
        ),
        param(
            {
                "local": "./local_path",
                "remote": "gs://bucket/key",
            },
            [Resolvable],
            Resolvable("./local_path", "gs://bucket/key"),
            does_not_raise(),
            id="dictionary parsed as gfs path resolvable",
        ),
        param(
            [
                {
                    "local": "./local_path",
                    "remote": "s3://bucket/key",
                }
            ],
            [S3Resolvable, Resolvable],
            None,
            raises(ValueError),
            id="Cannot parse list",
        ),
        param(
            {
                "remote": "gfs://4082e025bc2d7cb020b40b5fcefc62b86f0fe62c",
            },
            [S3Resolvable, Resolvable],
            None,
            raises(mm.ValidationError),
            id="Cannot parse dictionary",
        ),
    ],
)
def test__get_resolvable_from_value__parses_stuff(
    value: Any,
    resolvable_classes: list,
    expected: Optional[Tuple[str, str]],
    raises_error,
):
    with raises_error:
        actual = get_resolvable_from_value(value, resolvable_classes)
    if expected is not None:
        assert actual == expected


@mark.parametrize(
    "resolvable_class, value, default_local, default_remote, expected, raise_expectation",
    [
        param(
            S3Resolvable,
            S3Resolvable("/tmp/somefile", S3URI("s3://bucket/key")),
            None,
            None,
            S3Resolvable("/tmp/somefile", S3URI("s3://bucket/key")),
            does_not_raise(),
            id="object is returned as is",
        ),
        param(
            Uploadable,
            {"remote": "s3://bucket/key"},
            "/tmp/somefile",
            None,
            Uploadable("/tmp/somefile", "s3://bucket/key"),
            does_not_raise(),
            id="default local fills missing local in input",
        ),
        param(
            Uploadable,
            {"remote": "s3://bucket/key"},
            None,
            None,
            None,
            raises(ValueError, match=r"Local is None for .*\. No default provided"),
            id="ERROR: no local in input or default",
        ),
        param(
            S3Resolvable,
            42,
            None,
            None,
            None,
            raises(ValueError),
            id="ERROR: invalid type",
        ),
    ],
)
def test__from_any__works_as_intended(
    resolvable_class: Type[R],
    value: Any,
    default_local: Optional[str],
    default_remote: Optional[str],
    expected: Optional[Resolvable],
    raise_expectation,
):
    with raise_expectation:
        actual = resolvable_class.from_any(
            value=value, default_local=default_local, default_remote=default_remote
        )
    if expected is not None:
        assert actual == expected


@mark.parametrize(
    "value, expected, raise_expectation",
    [
        param(
            "s3://bucket/key",
            S3Resolvable("tmp558ca153", S3URI("s3://bucket/key")),
            does_not_raise(),
            id="Simple s3 path",
        ),
        param(
            "s3://bucket/key @ /tmp/somefile",
            S3Resolvable("/tmp/somefile", S3URI("s3://bucket/key")),
            does_not_raise(),
            id="Simple s3 path to local file",
        ),
        param(
            "/tmp/somefile @ s3://bucket/key",
            Uploadable("/tmp/somefile", S3URI("s3://bucket/key")),
            does_not_raise(),
            id="local file to Simple s3 path",
        ),
    ],
)
def test__from_str__works(value: str, expected: Resolvable, raise_expectation):
    with raise_expectation:
        actual = expected.from_str(value)
        assert actual == expected


@mark.parametrize(
    "value, expected, raise_expectation",
    [
        param(
            Uploadable("/tmp/somefile", S3URI("s3://bucket/key")),
            "/tmp/somefile @ s3://bucket/key",
            does_not_raise(),
            id="local file to Simple s3 path",
        ),
        param(
            S3Resolvable("/tmp/somefile", S3URI("s3://bucket/key")),
            "s3://bucket/key @ /tmp/somefile",
            does_not_raise(),
            id="Simple s3 path to local file",
        ),
    ],
)
def test__to_str__works(value: Resolvable, expected: str, raise_expectation):
    with raise_expectation:
        actual = value.to_str()
        assert actual == expected
