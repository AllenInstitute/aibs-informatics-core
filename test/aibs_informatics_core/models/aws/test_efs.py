from pathlib import Path
from typing import Optional

from aibs_informatics_test_resources import does_not_raise
from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.core import AWSRegion
from aibs_informatics_core.models.aws.efs import (
    AccessPointId,
    EFSPath,
    FileSystemDNSName,
    FileSystemId,
)

AP_ID = "fsap-1234567890abcdef0"
FS_ID = "fs-1234567890abcdef0"
FS_DNS_NAME = "fs-1234567890abcdef0.efs.us-east-1.amazonaws.com"

ANOTHER_FS_ID = "fs-1234567890abcdef1"


@mark.parametrize(
    "value, expected_id, expected_region, expected_arn, raise_expectation",
    [
        param(
            FS_ID,
            FS_ID,
            None,
            None,
            does_not_raise(),
            id="handles bare id",
        ),
        param(
            f"arn:aws:elasticfilesystem:us-east-1:123456789012:file-system/{FS_ID}",
            FS_ID,
            "us-east-1",
            "arn:aws:elasticfilesystem:us-east-1:123456789012:file-system/",
            does_not_raise(),
            id="handles arn",
        ),
        param(
            f"arn:aws:elasticfilesystem:us-east-1::file-system/{FS_ID}",
            None,
            None,
            None,
            raises(ValidationError),
            id="invalid: missing account",
        ),
        param(
            "fs1234567890abcdef",
            None,
            None,
            None,
            raises(ValidationError),
            id="invalid: missing prefix",
        ),
    ],
)
def test__FileSystemId__validation(
    value, expected_id, expected_region, expected_arn, raise_expectation
):
    with raise_expectation:
        actual = FileSystemId(value)

    if expected_id:
        assert actual.resource_id == expected_id
        assert actual.normalized == expected_id
        assert actual.region == expected_region
        assert actual.arn_prefix == expected_arn


@mark.parametrize(
    "value, expected_id, expected_region, expected_arn, raise_expectation",
    [
        param(
            AP_ID,
            AP_ID,
            None,
            None,
            does_not_raise(),
            id="handles bare id",
        ),
        param(
            f"arn:aws:elasticfilesystem:us-east-1:123456789012:access-point/{AP_ID}",
            AP_ID,
            "us-east-1",
            "arn:aws:elasticfilesystem:us-east-1:123456789012:access-point/",
            does_not_raise(),
            id="handles arn",
        ),
        param(
            f"arn:aws:elasticfilesystem:us-east-1::access-point/{AP_ID}",
            None,
            None,
            None,
            raises(ValidationError),
            id="invalid: missing account",
        ),
        param(
            "ap-1234567890abcdef",
            None,
            None,
            None,
            raises(ValidationError),
            id="invalid: missing prefix",
        ),
    ],
)
def test__AccessPointId__validation(
    value, expected_id, expected_region, expected_arn, raise_expectation
):
    with raise_expectation:
        actual = AccessPointId(value)

    if expected_id:
        assert actual.resource_id == expected_id
        assert actual.normalized == expected_id
        assert actual.region == expected_region
        assert actual.arn_prefix == expected_arn


@mark.parametrize(
    "value, expected_id, expected_region, raise_expectation",
    [
        param(
            FS_DNS_NAME,
            FS_ID,
            "us-east-1",
            does_not_raise(),
            id="handles dns name",
        ),
        param(
            f"{FS_ID}.efs.useast12.amazonaws.com",
            None,
            None,
            raises(ValidationError),
            id="invalid region",
        ),
        param(
            f"{FS_ID}.efs.amazonaws.com",
            None,
            None,
            raises(ValidationError),
            id="missing region",
        ),
    ],
)
def test__FileSystemDNSName__validation(value, expected_id, expected_region, raise_expectation):
    with raise_expectation:
        actual = FileSystemDNSName(value)

    if expected_id:
        assert actual.file_system_id == expected_id
        assert actual.region == expected_region


def test__FileSystemDNSName__build__works():
    actual = FileSystemDNSName.build(FS_ID, AWSRegion("us-east-1"))
    assert actual == FileSystemDNSName(f"{FS_ID}.efs.us-east-1.amazonaws.com")


@mark.parametrize(
    "value, expected_file_system_id, expected_path, raise_expectation",
    [
        param(
            f"efs://{FS_DNS_NAME}",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles efs://<fs-dns> (implicit path)",
        ),
        param(
            f"efs://{FS_DNS_NAME}/",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles efs://<fs-dns>/",
        ),
        param(
            f"efs://{FS_DNS_NAME}:/path/to/file.txt",
            FS_ID,
            Path("/path/to/file.txt"),
            does_not_raise(),
            id="handles efs://<fs-dns>:/path/to/file.txt",
        ),
        param(
            f"{FS_DNS_NAME}:",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles <fs-dns>:",
        ),
        param(
            f"{FS_DNS_NAME}:/",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles <fs-dns>:/",
        ),
        param(
            f"{FS_DNS_NAME}:/path/to/file.txt",
            FS_ID,
            Path("/path/to/file.txt"),
            does_not_raise(),
            id="handles <fs-dns>:/path/to/file.txt",
        ),
        param(
            f"efs://{FS_ID}",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles efs://<fs-id> (implicit path)",
        ),
        param(
            f"efs://{FS_ID}/",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles efs://<fs-id>/",
        ),
        param(
            f"efs://{FS_ID}:/",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles efs://<fs-id>:/",
        ),
        param(
            f"efs://{FS_ID}:/path/to/file.txt",
            FS_ID,
            Path("/path/to/file.txt"),
            does_not_raise(),
            id="handles efs://<fs-id>:/path/to/file.txt",
        ),
        param(
            f"{FS_ID}:",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles <fs-id>:",
        ),
        param(
            f"{FS_ID}:/",
            FS_ID,
            Path("/"),
            does_not_raise(),
            id="handles <fs-id>:/",
        ),
        param(
            f"{FS_ID}:/path/to/file.txt",
            FS_ID,
            Path("/path/to/file.txt"),
            does_not_raise(),
            id="handles <fs-id>:/path/to/file.txt",
        ),
        # invalid cases
        param(
            f"{FS_DNS_NAME}/path/to/file.txt",
            None,
            None,
            raises(ValidationError),
            id="invalid: <fs-dns>/path/to/file.txt (missing efs:// when : is not found)",
        ),
        param(
            f"{FS_ID}/path/to/file.txt",
            None,
            None,
            raises(ValidationError),
            id="invalid: <fs-id>/path/to/file.txt (missing efs:// when : is not found)",
        ),
        param(
            f"{AP_ID}/",
            None,
            None,
            raises(ValidationError),
            id="invalid: <ap-id>/ (missing efs:// when : is not found)",
        ),
    ],
)
def test__EFSPath__validation(value, expected_file_system_id, expected_path, raise_expectation):
    with raise_expectation:
        actual = EFSPath(value)

    if expected_path:
        assert actual.file_system_id == expected_file_system_id
        assert actual.path == expected_path


def test__EFSPath__eq__works():
    p1 = EFSPath(f"efs://{FS_ID}:/path/to/file.txt")
    p2 = EFSPath(f"efs://{FS_ID}/path/to/file.txt")
    p3 = EFSPath(f"{FS_ID}:/path/to/file.txt")
    p4 = EFSPath(f"{FS_DNS_NAME}:/path/to/file.txt")

    assert p1 == p2
    assert p1 == p3
    assert p1 == p4
    assert p2 == p3
    assert p2 == p4
    assert p3 == p4

    assert p1 != EFSPath(f"efs://{ANOTHER_FS_ID}:/path/to/file.txt")

    # Test different types
    assert not p1.__eq__("123")


@mark.parametrize(
    "this, other, expected, raise_expectation",
    [
        param(
            EFSPath.build(FS_ID, "/"),
            "/path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root / absolute str path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            "path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root / relative str path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            Path("/path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root / absolute Path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            Path("path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root / relative Path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            EFSPath.build(ANOTHER_FS_ID, "path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root / EFSPath",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            "/path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/dir/path/to/file.txt"),
            does_not_raise(),
            id="subdir / absolute str path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            "path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/dir/path/to/file.txt"),
            does_not_raise(),
            id="subdir / relative str path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            Path("/path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/dir/path/to/file.txt"),
            does_not_raise(),
            id="subdir / absolute Path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            Path("path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/dir/path/to/file.txt"),
            does_not_raise(),
            id="subdir / relative Path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            EFSPath.build(ANOTHER_FS_ID, "path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/dir/path/to/file.txt"),
            does_not_raise(),
            id="subdir / EFSPath",
        ),
    ],
)
def test__EFSPath__truediv__works(
    this: EFSPath, other, expected: Optional[EFSPath], raise_expectation
):
    with raise_expectation:
        actual = this / other

    if expected:
        assert actual == expected


@mark.parametrize(
    "this, other, expected, raise_expectation",
    [
        param(
            EFSPath.build(FS_ID, "/"),
            "/path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root // absolute str path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            "path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root // relative str path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            Path("/path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root // absolute Path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            Path("path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root // relative Path",
        ),
        param(
            EFSPath.build(FS_ID, "/"),
            EFSPath.build(ANOTHER_FS_ID, "path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="root // EFSPath",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            "/path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="subdir // absolute str path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            "path/to/file.txt",
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="subdir // relative str path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            Path("/path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="subdir // absolute Path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            Path("path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="subdir // relative Path",
        ),
        param(
            EFSPath.build(FS_ID, "/dir"),
            EFSPath.build(ANOTHER_FS_ID, "path/to/file.txt"),
            EFSPath(f"efs://{FS_ID}:/path/to/file.txt"),
            does_not_raise(),
            id="subdir // EFSPath",
        ),
    ],
)
def test__EFSPath__floordiv__works(
    this: EFSPath, other, expected: Optional[EFSPath], raise_expectation
):
    with raise_expectation:
        actual = this // other

    if expected:
        assert actual == expected


@mark.parametrize(
    "this, other, expected, raise_expectation",
    [
        param(
            EFSPath.build(ANOTHER_FS_ID, "path"),
            FS_ID,
            EFSPath(f"efs://{FS_ID}:/path"),
            does_not_raise(),
            id="other fs id",
        ),
        param(
            EFSPath.build(ANOTHER_FS_ID, "path"),
            FS_DNS_NAME,
            EFSPath(f"efs://{FS_ID}:/path"),
            does_not_raise(),
            id="other dns name",
        ),
        param(
            EFSPath.build(ANOTHER_FS_ID, "dir"),
            EFSPath.build(FS_ID, "path"),
            EFSPath(f"efs://{FS_ID}:/path/dir"),
            does_not_raise(),
            id="other efs path",
        ),
        param(
            EFSPath.build(FS_ID, "path"),
            Path("prefix"),
            EFSPath(f"efs://{FS_ID}:/prefix/path"),
            does_not_raise(),
            id="other path",
        ),
    ],
)
def test__EFSPath__rtruediv__works(
    this: EFSPath, other, expected: Optional[EFSPath], raise_expectation
):
    with raise_expectation:
        actual = this.__rtruediv__(other)

    if expected:
        assert actual == expected


def test__EFSPath_as_dns_uri__works():
    path = EFSPath.build(FS_ID, "/path/to/file.txt")
    assert path.as_dns_uri(AWSRegion("us-east-1")) == f"efs://{FS_DNS_NAME}:/path/to/file.txt"


def test__EFSPath_build__handles_DNSName():
    path = EFSPath.build(FileSystemDNSName(FS_DNS_NAME), "/path/to/file.txt")
    assert path == EFSPath(f"efs://{FS_DNS_NAME}:/path/to/file.txt")


def test__EFSPath_build__handles_FileSystemId():
    path = EFSPath.build(FileSystemId(FS_ID), "/path/to/file.txt")
    assert path == EFSPath(f"efs://{FS_ID}:/path/to/file.txt")


def test__EFSPath_build__invalid_id_raises_error():
    with raises(ValueError):
        EFSPath.build("invalid_id", "/path/to/file.txt")
