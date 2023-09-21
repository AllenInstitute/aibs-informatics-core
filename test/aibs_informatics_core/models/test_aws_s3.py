from contextlib import nullcontext as does_not_raise
from typing import Union

import marshmallow as mm
import pytest

from aibs_informatics_core.models.aws.s3 import S3URI, S3StorageClass


@pytest.mark.parametrize(
    "test_input, full_validate, expected, raise_expectation",
    [
        pytest.param(
            # test_input
            "s3://bucket-name/",
            # full_validate
            True,
            # expected
            {
                "bucket": "bucket-name",
                "key": "",
                "name": "",
                "parent": "s3://bucket-name/",
            },
            # raise_expectation
            does_not_raise(),
            id="Basic mock uri input bucket only (no key)",
        ),
        pytest.param(
            # test_input
            "s3://bucket-name",
            # full_validate
            True,
            # expected
            {
                "bucket": "bucket-name",
                "key": "",
                "name": "",
                "parent": "s3://bucket-name/",
            },
            # raise_expectation
            does_not_raise(),
            id="Basic mock uri input bucket only (no key) and no trailing slash",
        ),
        pytest.param(
            # test_input
            "s3://bucket-name/key-name",
            # full_validate
            True,
            # expected
            {
                "bucket": "bucket-name",
                "key": "key-name",
                "name": "key-name",
                "parent": "s3://bucket-name/",
            },
            # raise_expectation
            does_not_raise(),
            id="Basic mock uri input",
        ),
        pytest.param(
            # test_input
            "s3://genomics-file-store-us-west-2-076747868072/TESTSAMPLE_S01_L003_I1_001.fastq.gz",
            # full_validate
            True,
            # expected
            {
                "bucket": "genomics-file-store-us-west-2-076747868072",
                "key": "TESTSAMPLE_S01_L003_I1_001.fastq.gz",
                "name": "TESTSAMPLE_S01_L003_I1_001.fastq.gz",
                "parent": "s3://genomics-file-store-us-west-2-076747868072/",
            },
            # raise_expectation
            does_not_raise(),
            id="Realistic uri (representing s3 object) input",
        ),
        pytest.param(
            # test_input
            "s3://genomics-file-store-us-west-2-076747868072/36f41033-64a1-4038-8fd2-f3c5c8c53698",
            # full_validate
            True,
            # expected
            {
                "bucket": "genomics-file-store-us-west-2-076747868072",
                "key": "36f41033-64a1-4038-8fd2-f3c5c8c53698",
                "name": "36f41033-64a1-4038-8fd2-f3c5c8c53698",
                "parent": "s3://genomics-file-store-us-west-2-076747868072/",
            },
            # raise_expectation
            does_not_raise(),
            id="Realistic uri (representing s3 prefix) input",
        ),
        pytest.param(
            # test_input
            "s3://genomics-file-store//36f41033//64a1//4038//8fd2//f3c5c8c53698",
            # full_validate
            True,
            # expected
            {
                "bucket": "genomics-file-store",
                "key": "36f41033/64a1/4038/8fd2/f3c5c8c53698",
                "name": "f3c5c8c53698",
                "parent": "s3://genomics-file-store/36f41033/64a1/4038/8fd2/",
            },
            # raise_expectation
            does_not_raise(),
            id="URI with redundant slashes in key",
        ),
        pytest.param(
            # test_input
            "s3:///genomics-file-store/test-path",
            # full_validate
            True,
            # expected
            {
                "bucket": "genomics-file-store",
                "key": "test-path",
            },
            # raise_expectation
            does_not_raise(),
            id="URI with redundant slashes after host",
        ),
        pytest.param(
            # test_input
            "s3://${Token[detail-requestParameters-bucketName.2805]}/${Token[detail-requestParameters-key.2806]}",
            # full_validate,
            False,
            # expected
            {
                "bucket": "${Token[detail-requestParameters-bucketName.2805]}",
                "key": "${Token[detail-requestParameters-key.2806]}",
            },
            does_not_raise(),
            id="URI with env_var interpolation and periods/dashes succeeds with full_validate=False",
        ),
        pytest.param(
            # test_input
            "s3://${MY_ENV_VAR}/key-name",
            # full_validate
            True,
            # expected
            None,
            # raise_expectation
            pytest.raises(mm.ValidationError, match="is not a valid internal style 's3://' URI!"),
            id="URI with env_var interpolation fails with full_validate=True",
        ),
        pytest.param(
            # test_input
            "s3://${MY_ENV_VAR}/key-name",
            # full_validate
            False,
            # expected
            None,
            # raise_expectation
            does_not_raise(),
            id="URI with env_var interpolation succeeds with full_validate=False",
        ),
        pytest.param(
            # test_input
            "s3://bucket_name/key-name",
            # full_validate
            True,
            # expected
            None,
            # raise_expectation
            pytest.raises(mm.ValidationError, match="is not a valid internal style 's3://' URI!"),
            id="Invalid URI (contains '_') is rejected",
        ),
        pytest.param(
            # test_input
            "S3://bucket-name/key-name",
            # full_validate
            True,
            # expected
            None,
            # raise_expectation
            pytest.raises(mm.ValidationError, match="S3URI should start with 's3://'"),
            id="Incorrectly capitalized S3 URI scheme",
        ),
    ],
)
def test_s3uri_init(test_input, full_validate, expected, raise_expectation):
    with raise_expectation:
        obt = S3URI(test_input, full_validate=full_validate)

    if expected:
        for k, v in expected.items():
            assert v == getattr(obt, k)


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
            id="Basic build S3URI test case",
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
def test_s3uri_build(input_bucket, input_key, expected):
    obt = S3URI.build(bucket_name=input_bucket, key=input_key)
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
            id="Test S3URI.as_hosted_s3_url basic case",
        ),
        pytest.param(
            # current_uri
            "s3://my-bucket/my-key",
            # aws_region
            "us-east-1",
            # expected
            "https://my-bucket.s3.us-east-1.amazonaws.com/my-key",
            id="Test creation with another region",
        ),
    ],
)
def test_s3uri_as_hosted_s3_url(current_uri, aws_region, expected):
    s3_uri = S3URI(current_uri)
    obt = s3_uri.as_hosted_s3_url(aws_region=aws_region)
    assert expected == obt


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            "another-key",
            S3URI("s3://my-bucket/my-keyanother-key"),
            id="adds str",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/my-keyanother-key"),
            id="adds s3 uri",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key/"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/my-key/another-key"),
            id="adds s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__add__works(this: S3URI, other: Union[str, S3URI], expected: S3URI):
    assert this + other == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            "another-key",
            S3URI("s3://my-bucket/my-key/another-key"),
            id="this / str",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/my-key/another-key"),
            id="this / s3 uri",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key/"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/my-key/another-key"),
            id="this / s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__truediv__works(this: S3URI, other: Union[str, S3URI], expected: S3URI):
    assert this / other == expected


@pytest.mark.parametrize(
    "this, other, expected",
    [
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            "another-key",
            S3URI("s3://my-bucket/another-key"),
            id="this // str",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/another-key"),
            id="this // s3 uri",
        ),
        pytest.param(
            S3URI("s3://my-bucket/my-key/"),
            S3URI("s3://another-bucket/another-key"),
            S3URI("s3://my-bucket/another-key"),
            id="this // s3 uri with trailing slash",
        ),
    ],
)
def test__S3URI__floordiv__works(this: S3URI, other: Union[str, S3URI], expected: S3URI):
    assert this // other == expected


# @pytest.mark.parametrize(
#     "s3_object_fixture, expected",
#     [
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.STANDARD.value},
#             # expected
#             S3StorageClass.STANDARD,
#             id="Test S3StorageClass.from_boto_s3_obj - STANDARD storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.STANDARD_IA.value},
#             # expected
#             S3StorageClass.STANDARD_IA,
#             id="Test S3StorageClass.from_boto_s3_obj - STANDARD_IA storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.INTELLIGENT_TIERING.value},
#             # expected
#             S3StorageClass.INTELLIGENT_TIERING,
#             id="Test S3StorageClass.from_boto_s3_obj - INTELLIGENT_TIERING storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.ONEZONE_IA.value},
#             # expected
#             S3StorageClass.ONEZONE_IA,
#             id="Test S3StorageClass.from_boto_s3_obj - ONEZONE_IA storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.GLACIER_IR.value},
#             # expected
#             S3StorageClass.GLACIER_IR,
#             id="Test S3StorageClass.from_boto_s3_obj - GLACIER_IR storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.GLACIER.value},
#             # expected
#             S3StorageClass.GLACIER,
#             id="Test S3StorageClass.from_boto_s3_obj - GLACIER storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.DEEP_ARCHIVE.value},
#             # expected
#             S3StorageClass.DEEP_ARCHIVE,
#             id="Test S3StorageClass.from_boto_s3_obj - DEEP_ARCHIVE storage class",
#         ),
#         pytest.param(
#             # s3_object_fixture
#             {"mock_object_storage_class": S3StorageClass.REDUCED_REDUNDANCY.value},
#             # expected
#             S3StorageClass.REDUCED_REDUNDANCY,
#             id="Test S3StorageClass.from_boto_s3_obj - REDUCED_REDUNDANCY storage class",
#         ),
#     ],
#     indirect=["s3_object_fixture"],
# )
# def test__s3_storage_class__from_boto_s3_obj(s3_object_fixture, expected):
#     s3_obj = get_object(s3_object_fixture)
#     result = S3StorageClass.from_boto_s3_obj(s3_obj)
#     assert expected == result
