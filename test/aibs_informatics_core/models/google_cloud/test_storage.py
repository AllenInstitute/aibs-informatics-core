from pytest import mark, param

from aibs_informatics_core.models.google_cloud.storage import GCSPath


@mark.parametrize(
    "bucket, key, expected",
    [
        param("bucket", "key", "gs://bucket/key", id="Simple"),
        param("bucket", "key/with/slashes", "gs://bucket/key/with/slashes", id="With slashes"),
        param("bucket", "key with spaces", "gs://bucket/key%20with%20spaces", id="With spaces"),
    ],
)
def test__GCSPath__build__works(bucket, key, expected):
    actual = GCSPath.build(bucket=bucket, key=key)
    assert actual == expected
