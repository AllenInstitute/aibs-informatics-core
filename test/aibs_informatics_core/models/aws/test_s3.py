from contextlib import nullcontext as does_not_raise
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import pytest

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import (
    S3BucketName,
    S3BucketNamePlaceholder,
    S3CopyRequest,
    S3CopyResponse,
    S3Key,
    S3KeyPlaceholder,
    S3KeyPrefix,
    S3Path,
    S3PathPlaceholder,
    S3PathStats,
    S3RestoreStatus,
    S3RestoreStatusEnum,
    S3StorageClass,
    S3TransferRequest,
    S3TransferResponse,
    S3UploadRequest,
    S3UploadResponse,
)
from aibs_informatics_core.models.base import CustomStringField
from aibs_informatics_core.models.base.custom_fields import EnumField


def test__S3PathStats__getitem__works():
    stats = S3PathStats(datetime(2021, 1, 1, tzinfo=timezone.utc), 123, 456)
    assert stats["last_modified"] == stats.last_modified
    assert stats["size_bytes"] == stats.size_bytes
    assert stats["object_count"] == stats.object_count


@pytest.mark.parametrize(
    "string_input, allow_placeholders, expected, raise_expectation",
    [
        pytest.param(
            "s3://bucket-name/",
            False,
            {
                "bucket": "bucket-name",
                "key": "",
                "name": "",
                "parent": "s3://bucket-name/",
            },
            does_not_raise(),
            id="Basic s3 path input bucket only (no key)",
        ),
        pytest.param(
            "s3://bucket-name",
            False,
            # expected
            {
                "bucket": "bucket-name",
                "key": "",
                "name": "",
                "parent": "s3://bucket-name/",
            },
            # raise_expectation
            does_not_raise(),
            id="Basic s3 path input bucket only (no key) and no trailing slash",
        ),
        pytest.param(
            "s3://bucket-name/key-name",
            False,
            {
                "bucket": "bucket-name",
                "key": "key-name",
                "name": "key-name",
                "parent": "s3://bucket-name/",
            },
            does_not_raise(),
            id="Basic s3 path input",
        ),
        pytest.param(
            "s3://genomics-file-store-us-west-2-076747868072/TESTSAMPLE_S01_L003_I1_001.fastq.gz",
            False,
            {
                "bucket": "genomics-file-store-us-west-2-076747868072",
                "key": "TESTSAMPLE_S01_L003_I1_001.fastq.gz",
                "name": "TESTSAMPLE_S01_L003_I1_001.fastq.gz",
                "parent": "s3://genomics-file-store-us-west-2-076747868072/",
            },
            does_not_raise(),
            id="project s3 path input",
        ),
        pytest.param(
            "s3://genomics-file-store-us-west-2-076747868072/36f41033-64a1-4038-8fd2-f3c5c8c53698",
            False,
            {
                "bucket": "genomics-file-store-us-west-2-076747868072",
                "key": "36f41033-64a1-4038-8fd2-f3c5c8c53698",
                "name": "36f41033-64a1-4038-8fd2-f3c5c8c53698",
                "parent": "s3://genomics-file-store-us-west-2-076747868072/",
            },
            does_not_raise(),
            id="S3 path prefix input no trailing slash",
        ),
        pytest.param(
            "s3://genomics-file-store-us-west-2-076747868072/36f41033-64a1-4038-8fd2-f3c5c8c53698/",
            False,
            {
                "bucket": "genomics-file-store-us-west-2-076747868072",
                "key": "36f41033-64a1-4038-8fd2-f3c5c8c53698/",
                "name": "36f41033-64a1-4038-8fd2-f3c5c8c53698",
                "parent": "s3://genomics-file-store-us-west-2-076747868072/",
            },
            does_not_raise(),
            id="S3 path prefix input with trailing slash",
        ),
        pytest.param(
            "s3://genomics-file-store//36f41033//64a1//4038//8fd2//f3c5c8c53698",
            False,
            {
                "bucket": "genomics-file-store",
                "key": "36f41033/64a1/4038/8fd2/f3c5c8c53698",
                "name": "f3c5c8c53698",
                "parent": "s3://genomics-file-store/36f41033/64a1/4038/8fd2/",
            },
            does_not_raise(),
            id="URI with redundant slashes in key are removed",
        ),
        pytest.param(
            "s3://bucket-name/",
            True,
            {
                "bucket": "bucket-name",
                "key": "",
                "name": "",
                "parent": "s3://bucket-name/",
            },
            does_not_raise(),
            id="S3Path with empty key (just bucket name) and full_validate=True",
        ),
        pytest.param(
            "s3://bucket-name/folder1/folder2/",
            True,
            {
                "bucket": "bucket-name",
                "key": "folder1/folder2/",
                "name": "folder2",
                "parent": "s3://bucket-name/folder1/",
            },
            does_not_raise(),
            id="S3Path with empty key (just bucket name) and full_validate=True",
        ),
        pytest.param(
            # test_input
            "s3:///genomics-file-store/test-path",
            False,
            {
                "bucket": "genomics-file-store",
                "key": "test-path",
            },
            does_not_raise(),
            id="S3 path with redundant slashes after host",
        ),
        pytest.param(
            "s3://${Token[detail-requestParameters-bucketName.2805]}/${Token[detail-requestParameters-key.2806]}",
            True,
            {
                "bucket": "${Token[detail-requestParameters-bucketName.2805]}",
                "key": "${Token[detail-requestParameters-key.2806]}",
            },
            does_not_raise(),
            id="S3 path with cdk-style placeholders succeeds with allow_placeholders=True",
        ),
        pytest.param(
            "s3://${Token[detail-requestParameters-bucketName.2805]}/${Token[detail-requestParameters-key.2806]}",
            False,
            None,
            pytest.raises(ValidationError),
            id="S3 path with cdk-style placeholders fails with allow_placeholders=False - (fail)",
        ),
        pytest.param(
            "s3://${MY_ENV_VAR}/keyprefix/${MY_ENV_VAR2}/key-name",
            True,
            {
                "bucket": "${MY_ENV_VAR}",
                "key": "keyprefix/${MY_ENV_VAR2}/key-name",
                "parent": "s3://${MY_ENV_VAR}/keyprefix/${MY_ENV_VAR2}/",
            },
            does_not_raise(),
            id="S3 path with simple env_var interpolation succeeds with allow_placeholders=True",
        ),
        pytest.param(
            "s3://${MY_ENV_VAR}/keyprefix/${MY_ENV_VAR2}/key-name",
            False,
            None,
            pytest.raises(ValidationError),
            id="S3 path with simple env_var interpolation fails with allow_placeholders=False - (fail)",  # noqa: E501
        ),
        pytest.param(
            "s3://bucket_name/key-name",
            False,
            None,
            pytest.raises(ValidationError),
            id="Invalid s3 bucket name (contains '_') is rejected - (fail)",
        ),
        pytest.param(
            "S3://bucket-name/key-name",
            False,
            None,
            pytest.raises(ValidationError),
            id="Incorrectly capitalized S3 URI scheme - (fail)",
        ),
    ],
)
def test__S3Path__init(string_input, allow_placeholders, expected, raise_expectation):
    with raise_expectation:
        s3_path = S3Path(string_input)
        s3_path_placeholder = S3PathPlaceholder(
            string_input, allow_placeholders=allow_placeholders
        )

    if expected:
        for k, v in expected.items():
            assert v == getattr(s3_path, k), (
                f"Expected {k} to be {v}, but got {getattr(s3_path, k)}"
            )
            assert v == getattr(s3_path_placeholder, k), (
                f"Expected {k} to be {v}, but got {getattr(s3_path, k)}"
            )
        assert s3_path_placeholder.allow_placeholders == allow_placeholders


def test__S3PathPlaceholder__full_validate__backwards_compatibility():
    # NOTE: This should be removed in the future
    with pytest.raises(ValidationError):
        S3PathPlaceholder("s3://bucket-name/${key-name}", full_validate=True)

    with does_not_raise():
        S3PathPlaceholder("s3://bucket-name/${key-name}", full_validate=False)

    with pytest.raises(ValidationError):
        S3PathPlaceholder.build("bucket-name", "${key-name}", full_validate=True)

    with does_not_raise():
        S3PathPlaceholder.build("bucket-name", "${key-name}", full_validate=False)


@pytest.mark.parametrize(
    "input_bucket, input_key, expected",
    [
        pytest.param(
            # input_bucket
            "bucket-mcbucketface",
            # input_key
            "key-mckeyface",
            # expected
            "s3://bucket-mcbucketface/key-mckeyface",
            id="Basic build S3Path test case",
        ),
        pytest.param(
            # input_bucket
            "my-cool-bucket",
            # input_key
            "/my-cooler-key",
            # expected
            "s3://my-cool-bucket/my-cooler-key",
            id="Test key leading slash '/' characters are removed",
        ),
    ],
)
def test__S3URI__build(input_bucket, input_key, expected):
    obt = S3Path.build(bucket_name=input_bucket, key=input_key)
    assert expected == obt


@pytest.mark.parametrize(
    "current_uri, aws_region, expected",
    [
        pytest.param(
            # current_uri
            "s3://my-bucket/my-key",
            # aws_region
            "us-west-2",
            # expected
            "https://my-bucket.s3.us-west-2.amazonaws.com/my-key",
            id="basic case",
        ),
        pytest.param(
            # current_uri
            "s3://my-bucket/my-key",
            # aws_region
            "us-east-1",
            # expected
            "https://my-bucket.s3.us-east-1.amazonaws.com/my-key",
            id="handles another region",
        ),
        pytest.param(
            # current_uri
            "s3://my-bucket/my-key/with space",
            # aws_region
            "us-west-2",
            # expected
            "https://my-bucket.s3.us-west-2.amazonaws.com/my-key/with%20space",
            id="encodes spaces in key",
        ),
    ],
)
def test__S3Path__as_hosted_s3_url(current_uri, aws_region, expected):
    s3_uri = S3Path(current_uri)
    obt = s3_uri.as_hosted_s3_url(aws_region=aws_region)
    assert expected == obt


@pytest.mark.parametrize(
    "value, raise_expectation",
    [
        pytest.param("mybucket", does_not_raise(), id="(o) basic case"),
        pytest.param("abc", does_not_raise(), id="(o) minimum length"),
        pytest.param("a" * 63, does_not_raise(), id="(o) maximum length"),
        pytest.param("my-bucket-name", does_not_raise(), id="(o) hyphenated in middle"),
        pytest.param("my.bucket.name", does_not_raise(), id="(o) dotted in middle"),
        # invalid cases
        pytest.param("my", pytest.raises(ValidationError), id="(x) too short"),
        pytest.param("a" * 64, pytest.raises(ValidationError), id="(x) too long"),
        pytest.param("my${bucket}", pytest.raises(ValidationError), id="(x) contains placeholder"),
        pytest.param(
            "my_bucket_name", pytest.raises(ValidationError), id="(x) contains underscore"
        ),
        pytest.param("my-bucket-name-", pytest.raises(ValidationError), id="(x) trailing hyphen"),
        pytest.param("-my-bucket-name", pytest.raises(ValidationError), id="(x) leading hyphen"),
        pytest.param("my-bucket-name.", pytest.raises(ValidationError), id="(x) trailing period"),
        pytest.param(".my-bucket-name", pytest.raises(ValidationError), id="(x) leading period"),
        pytest.param("${token}", pytest.raises(ValidationError), id="(x) is placeholder"),
    ],
)
def test__S3BucketName__init_no_placeholders(value: str, raise_expectation):
    with raise_expectation:
        S3BucketName(value)
        S3BucketNamePlaceholder(value, allow_placeholders=False)


@pytest.mark.parametrize(
    "value, raise_expectation",
    [
        pytest.param("mybucket", does_not_raise(), id="(o) basic case"),
        pytest.param("abc", does_not_raise(), id="(o) minimum length"),
        pytest.param("a" * 63, does_not_raise(), id="(o) maximum length"),
        pytest.param("my-bucket-name", does_not_raise(), id="(o) hyphenated in middle"),
        pytest.param("my.bucket.name", does_not_raise(), id="(o) dotted in middle"),
        pytest.param("${bucket}", does_not_raise(), id="(o) placeholder"),
        pytest.param("m${bucket}", does_not_raise(), id="(o) trailing placeholder"),
        pytest.param("${bucket}m", does_not_raise(), id="(o) leading placeholder"),
        pytest.param("${bucket}${bucket}", does_not_raise(), id="(o) multiple placeholders"),
        pytest.param(
            "my.${bucket}.name${bucket}", does_not_raise(), id="(o) multiple placeholders and dots"
        ),
        # invalid cases
        pytest.param("my", pytest.raises(ValidationError), id="(x) too short"),
        pytest.param("a" * 64, pytest.raises(ValidationError), id="(x) too long"),
        pytest.param(
            "my_bucket_name", pytest.raises(ValidationError), id="(x) contains underscore"
        ),
        pytest.param("my-bucket-name-", pytest.raises(ValidationError), id="(x) trailing hyphen"),
        pytest.param("-my-bucket-name", pytest.raises(ValidationError), id="(x) leading hyphen"),
        pytest.param("my-bucket-name.", pytest.raises(ValidationError), id="(x) trailing period"),
        pytest.param(".my-bucket-name", pytest.raises(ValidationError), id="(x) leading period"),
        pytest.param(
            "-${token}", pytest.raises(ValidationError), id="(x) leading hyphen before placeholder"
        ),
        pytest.param(
            "${token}-", pytest.raises(ValidationError), id="(x) trailing hyphen after placeholder"
        ),
    ],
)
def test__S3BucketName__init_allow_placeholders(value: str, raise_expectation):
    with raise_expectation:
        S3BucketNamePlaceholder(value, allow_placeholders=True)


@pytest.mark.parametrize(
    "value, raise_expectation",
    [
        pytest.param("key", does_not_raise(), id="(o) basic case"),
        pytest.param("a/b/c", does_not_raise(), id="(o) multiple slashes"),
        pytest.param("a/b/c/", does_not_raise(), id="(o) trailing slash"),
        pytest.param("", does_not_raise(), id="(o) minimum length"),
        pytest.param("a&$@=;:/+ ,?", does_not_raise(), id="(o) special characters"),
        # invalid cases
        pytest.param("${token}", pytest.raises(ValidationError), id="(x) placeholder"),
        pytest.param("a%23", pytest.raises(ValidationError), id="(x) percent encoded"),
        pytest.param("a\\c", pytest.raises(ValidationError), id="(x) backslash"),
        pytest.param("a{b", pytest.raises(ValidationError), id="(x) open brace"),
        pytest.param("a}b", pytest.raises(ValidationError), id="(x) close brace"),
        pytest.param("a|b", pytest.raises(ValidationError), id="(x) pipe"),
        pytest.param("a[b", pytest.raises(ValidationError), id="(x) open bracket"),
        pytest.param("a]b", pytest.raises(ValidationError), id="(x) close bracket"),
        pytest.param("a^b", pytest.raises(ValidationError), id="(x) caret"),
        pytest.param("a`b", pytest.raises(ValidationError), id="(x) backtick"),
        pytest.param("a~b", pytest.raises(ValidationError), id="(x) tilde"),
        pytest.param("a<>b", pytest.raises(ValidationError), id="(x) less / greater than"),
        pytest.param("a#b", pytest.raises(ValidationError), id="(x) pound"),
    ],
)
def test__S3Key__init_no_placeholders(value: str, raise_expectation):
    with raise_expectation:
        S3Key(value)
        S3KeyPlaceholder(value, allow_placeholders=False)


@pytest.mark.parametrize(
    "value, raise_expectation",
    [
        pytest.param("key", does_not_raise(), id="(o) basic case"),
        pytest.param("a/b/c", does_not_raise(), id="(o) multiple slashes"),
        pytest.param("a/b/c/", does_not_raise(), id="(o) trailing slash"),
        pytest.param("", does_not_raise(), id="(o) minimum length"),
        pytest.param("a&$@=;:/+ ,?", does_not_raise(), id="(o) special characters"),
        pytest.param("${key}", does_not_raise(), id="(o) placeholder"),
        pytest.param("abc/${key}", does_not_raise(), id="(o) trailing placeholder"),
        pytest.param("${key}key/key", does_not_raise(), id="(o) leading placeholder"),
        pytest.param("${key1}${key2}", does_not_raise(), id="(o) multiple placeholders"),
        pytest.param("${key1}/${key2}", does_not_raise(), id="(o) multiple placeholders with /"),
        # invalid cases
        pytest.param("a%23", pytest.raises(ValidationError), id="(x) percent encoded"),
        pytest.param("a\\c", pytest.raises(ValidationError), id="(x) backslash"),
        pytest.param("a{b", pytest.raises(ValidationError), id="(x) open brace"),
        pytest.param("a}b", pytest.raises(ValidationError), id="(x) close brace"),
        pytest.param("a|b", pytest.raises(ValidationError), id="(x) pipe"),
        pytest.param("a[b", pytest.raises(ValidationError), id="(x) open bracket"),
        pytest.param("a]b", pytest.raises(ValidationError), id="(x) close bracket"),
        pytest.param("a^b", pytest.raises(ValidationError), id="(x) caret"),
        pytest.param("a`b", pytest.raises(ValidationError), id="(x) backtick"),
        pytest.param("a~b", pytest.raises(ValidationError), id="(x) tilde"),
        pytest.param("a<>b", pytest.raises(ValidationError), id="(x) less / greater than"),
        pytest.param("a#b", pytest.raises(ValidationError), id="(x) pound"),
    ],
)
def test__S3Key__init_allow_placeholders(value: str, raise_expectation):
    with raise_expectation:
        S3KeyPlaceholder(value, allow_placeholders=True)


@pytest.mark.parametrize(
    "this, other, expected, raise_expectation",
    [
        pytest.param(
            S3BucketName("my-bucket"),
            "my-key",
            S3Path("s3://my-bucket/my-key"),
            does_not_raise(),
            id="handles simple",
        ),
        pytest.param(
            S3BucketName("my-bucket"),
            "s3://another-bucket/another-key",
            S3Path("s3://my-bucket/another-key"),
            does_not_raise(),
            id="handles uri",
        ),
    ],
)
def test__S3BucketName__truediv__works(this: S3BucketName, other, expected, raise_expectation):
    with raise_expectation:
        actual = this / other

    assert actual == expected


@pytest.mark.parametrize(
    "this, expected",
    [
        pytest.param(
            S3Key("my-key"),
            ["my-key"],
            id="simple",
        ),
        pytest.param(
            S3Key("my/key"),
            ["my", "key"],
            id="handles empty",
        ),
        pytest.param(
            S3KeyPrefix("my/key/"),
            ["my", "key", ""],
            id="handles key prefix with trailing slash",
        ),
    ],
)
def test__S3Key__components(this: S3Key, expected):
    assert this.components == expected


@pytest.mark.parametrize(
    "this, other, expected, raise_expectation",
    [
        pytest.param(
            S3Key("my-key"),
            "another-key",
            S3Key("another-key/my-key"),
            does_not_raise(),
            id="handles simple",
        ),
        pytest.param(
            S3Key("my-key"),
            "",
            S3Key("my-key"),
            does_not_raise(),
            id="handles empty",
        ),
        pytest.param(
            S3Key("my-key"),
            "another-key/",
            S3Key("another-key/my-key"),
            does_not_raise(),
            id="handles key with slash",
        ),
        pytest.param(
            S3Key("my-key"),
            object(),
            None,
            pytest.raises(TypeError),
            id="raises for invalid type",
        ),
    ],
)
def test__S3Key__rtruediv__works(this: S3Key, other, expected, raise_expectation):
    with raise_expectation:
        actual = other / this

    if expected:
        assert actual == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            "another-key",
            S3Path("s3://my-bucket/my-keyanother-key"),
            id="adds str",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/my-keyanother-key"),
            id="adds s3 uri",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key/"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/my-key/another-key"),
            id="adds s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__add__works(this: S3Path, other: Union[str, S3Path], expected: S3Path):
    assert this + other == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            "another-key",
            S3Path("s3://my-bucket/my-key/another-key"),
            id="this / str",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/my-key/another-key"),
            id="this / s3 uri",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key/"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/my-key/another-key"),
            id="this / s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__truediv__works(this: S3Path, other: Union[str, S3Path], expected: S3Path):
    assert this / other == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            "another-bucket",
            S3Path("s3://another-bucket/my-key"),
            id="str / SELF",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            "s3://another-bucket/another-key",
            S3Path("s3://another-bucket/my-key"),
            id="s3 uri str / SELF",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            S3BucketName("another-bucket"),
            S3Path("s3://another-bucket/my-key"),
            id="s3 bucket name / SELF",
        ),
    ],
)
def test__S3URI__rtruediv__works(this: S3Path, other: Union[str, S3Path], expected: S3Path):
    assert other / this == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            "another-key",
            S3Path("s3://my-bucket/another-key"),
            id="this // str",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/another-key"),
            id="this // s3 uri",
        ),
        pytest.param(
            S3Path("s3://my-bucket/my-key/"),
            S3Path("s3://another-bucket/another-key"),
            S3Path("s3://my-bucket/another-key"),
            id="this // s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__floordiv__works(this: S3Path, other: Union[str, S3Path], expected: S3Path):
    assert this // other == expected


def test__S3URI__as_dict__works():
    assert S3Path("s3://my-bucket/my-key").as_dict() == {"Bucket": "my-bucket", "Key": "my-key"}


def test__S3URI__as_mm_field__works():
    assert isinstance(S3Path("s3://my-bucket/my-key").as_mm_field(), CustomStringField)


def test__S3URI__with_folder_suffix__works():
    this = S3Path("s3://my-bucket/my-key")
    expected = S3Path("s3://my-bucket/my-key/")
    assert this.with_folder_suffix == expected


@pytest.mark.parametrize(
    "s3_object_fixture, expected",
    [
        pytest.param(
            # s3_object_fixture
            {"storage_class": None},
            # expected
            S3StorageClass.STANDARD,
            id="Test S3StorageClass.from_boto_s3_obj - STANDARD storage class (None)",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.STANDARD.value},
            # expected
            S3StorageClass.STANDARD,
            id="Test S3StorageClass.from_boto_s3_obj - STANDARD storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.STANDARD_IA.value},
            # expected
            S3StorageClass.STANDARD_IA,
            id="Test S3StorageClass.from_boto_s3_obj - STANDARD_IA storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.INTELLIGENT_TIERING.value},
            # expected
            S3StorageClass.INTELLIGENT_TIERING,
            id="Test S3StorageClass.from_boto_s3_obj - INTELLIGENT_TIERING storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.ONEZONE_IA.value},
            # expected
            S3StorageClass.ONEZONE_IA,
            id="Test S3StorageClass.from_boto_s3_obj - ONEZONE_IA storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.GLACIER_IR.value},
            # expected
            S3StorageClass.GLACIER_IR,
            id="Test S3StorageClass.from_boto_s3_obj - GLACIER_IR storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.GLACIER.value},
            # expected
            S3StorageClass.GLACIER,
            id="Test S3StorageClass.from_boto_s3_obj - GLACIER storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.DEEP_ARCHIVE.value},
            # expected
            S3StorageClass.DEEP_ARCHIVE,
            id="Test S3StorageClass.from_boto_s3_obj - DEEP_ARCHIVE storage class",
        ),
        pytest.param(
            # s3_object_fixture
            {"storage_class": S3StorageClass.REDUCED_REDUNDANCY.value},
            # expected
            S3StorageClass.REDUCED_REDUNDANCY,
            id="Test S3StorageClass.from_boto_s3_obj - REDUCED_REDUNDANCY storage class",
        ),
    ],
)
def test__s3_storage_class__from_boto_s3_obj(s3_object_fixture, expected):
    class S3_Object:
        def __init__(self, storage_class):
            self.storage_class = storage_class

    s3_obj = S3_Object(**s3_object_fixture)
    result = S3StorageClass.from_boto_s3_obj(s3_obj)
    assert expected == result


def test__list_transitionable_storage_classes__works():
    assert S3StorageClass.STANDARD in S3StorageClass.list_transitionable_storage_classes()


def test__list_archive_storage_classes__works():
    assert S3StorageClass.GLACIER in S3StorageClass.list_archive_storage_classes()


def test__S3StorageClass__as_mm_field__works():
    assert isinstance(S3StorageClass.as_mm_field(), EnumField)


def test__S3RestoreStatus__works():
    assert S3RestoreStatus.from_raw_s3_restore_status(None) == S3RestoreStatus(
        S3RestoreStatusEnum.NOT_STARTED
    )
    assert S3RestoreStatus.from_raw_s3_restore_status('ongoing-request="true"') == S3RestoreStatus(
        S3RestoreStatusEnum.IN_PROGRESS
    )
    assert S3RestoreStatus.from_raw_s3_restore_status(
        'ongoing-request="false", expiry-date="Fri, 21 Dec 2012 00:00:00 GMT"'
    ) == S3RestoreStatus(
        S3RestoreStatusEnum.FINISHED,
        restore_expiration_time=datetime(2012, 12, 21, 0, 0, 0, 0, tzinfo=timezone.utc),
    )


def test__S3UploadResponse__fails_if_no_reason():
    with pytest.raises(ValueError):
        S3UploadResponse(
            request=S3UploadRequest(
                source_path=Path("/tmp/my-file"),
                destination_path=S3Path("s3://my-bucket/my-key"),
            ),
            failed=True,
            reason=None,
        )


def test__S3CopyResponse__fails_if_no_reason():
    with pytest.raises(ValueError):
        S3CopyResponse(
            request=S3CopyRequest(
                source_path=S3Path("s3://my-bucket/my-key"),
                destination_path=S3Path("s3://tmp/my-file"),
            ),
            failed=True,
            reason=None,
        )


def test__S3TransferResponse__fails_if_no_reason():
    with pytest.raises(ValueError):
        S3TransferResponse(
            request=S3TransferRequest(
                source_path=S3Path("s3://my-bucket/my-key"),
                destination_path=Path("/tmp/my-file"),
            ),
            failed=True,
            reason=None,
        )


def test__S3Path__parent__works():
    # Test with a key
    path = S3Path("s3://my-bucket/my-key")
    assert path.parent == S3Path("s3://my-bucket/")

    path = S3Path("s3://my-bucket/my-prefix/my-key")
    assert path.parent == S3Path("s3://my-bucket/my-prefix/")
    assert path.parent.parent == S3Path("s3://my-bucket/")
    assert path.parent.parent.parent == S3Path("s3://my-bucket/")  # Parent of bucket is itself

    # Test with a key prefix
    path = S3Path("s3://my-bucket/my-prefix/")
    assert path.parent == S3Path("s3://my-bucket/")

    # Test with just the bucket
    path = S3Path("s3://my-bucket/")
    assert path.parent == S3Path("s3://my-bucket/")  # Parent of bucket is itself
