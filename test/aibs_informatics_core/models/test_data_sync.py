from pathlib import Path


from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.data_sync import (
    BatchDataSyncRequest,
    DataSyncConfig,
    DataSyncRequest,
    DataSyncTask,
    JSONContent,
    JSONReference,
    PrepareBatchDataSyncResponse,
)

S3_URI = S3Path.build(bucket_name="bucket", key="key")
LOCAL_PATH = Path("/tmp/foo")


def test__JSONContent__from_dict():
    model_dict = {"content": {"foo": "bar"}}
    expected = JSONContent(content={"foo": "bar"})
    actual = JSONContent.from_dict(model_dict)
    assert actual == expected


def test__JSONContent__to_dict():
    model = JSONContent(content={"foo": "bar"})
    expected = {"content": {"foo": "bar"}}
    actual = model.to_dict()
    assert actual == expected


def test__JSONReference__from_dict__s3():
    model_dict = {"path": str(S3_URI)}
    expected = JSONReference(path=S3_URI)
    actual = JSONReference.from_dict(model_dict)
    assert actual == expected


def test__JSONReference__from_dict__local():
    model_dict = {"path": str(LOCAL_PATH)}
    expected = JSONReference(path=LOCAL_PATH)
    actual = JSONReference.from_dict(model_dict)
    assert actual.path == expected.path


def test__JSONReference__to_dict__s3():
    model = JSONReference(path=S3_URI)
    expected = {"path": str(S3_URI)}
    actual = model.to_dict()
    assert actual == expected


def test__JSONReference__to_dict__local():
    model = JSONReference(path=LOCAL_PATH)
    expected = {"path": str(LOCAL_PATH)}
    actual = model.to_dict()
    assert actual == expected


def test__DataSyncRequest__from_dict():
    model_dict = {
        "source_path": str(S3_URI),
        "destination_path": str(S3_URI),
        "retain_source_data": True,
    }
    expected = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        retain_source_data=True,
    )
    actual = DataSyncRequest.from_dict(model_dict)
    assert actual == expected


def test__DataSyncRequest__properties():
    request = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        retain_source_data=True,
    )
    assert request.config == DataSyncConfig(retain_source_data=True)
    assert request.task == DataSyncTask(
        source_path=S3_URI,
        destination_path=S3_URI,
    )


def test__BatchDataSyncRequest__from_dict():
    single_request = {
        "source_path": str(S3_URI),
        "destination_path": str(S3_URI),
        "source_path_prefix": "prefix",
    }
    model_dict = {
        "requests": [single_request],
    }
    expected = BatchDataSyncRequest(
        requests=[
            DataSyncRequest(
                source_path=S3_URI,
                destination_path=S3_URI,
                source_path_prefix=S3KeyPrefix("prefix"),
            ),
        ],
    )
    actual = BatchDataSyncRequest.from_dict(model_dict)
    assert actual == expected

    # handles single request
    actual = BatchDataSyncRequest.from_dict(single_request)
    assert actual == expected


def test__BatchDataSyncRequest__to_dict():
    request = BatchDataSyncRequest(
        requests=[
            DataSyncRequest(
                source_path=S3_URI,
                destination_path=S3_URI,
                source_path_prefix=S3KeyPrefix("prefix"),
            ),
        ],
    )
    expected = {
        "requests": [
            {
                "source_path": str(S3_URI),
                "destination_path": str(S3_URI),
                "source_path_prefix": "prefix",
                "fail_if_missing": True,
                "max_concurrency": 25,
                "require_lock": False,
                "force": False,
                "size_only": False,
                "retain_source_data": True,
                "include_detailed_response": False,
                "remote_to_local_config": {"use_custom_tmp_dir": False},
            },
        ],
        "allow_partial_failure": False,
    }
    actual = request.to_dict()
    assert actual == expected


def test__BatchDataSyncRequest__to_dict__s3_path():
    response = BatchDataSyncRequest(
        requests=S3_URI,
    )
    expected = {
        "requests": str(S3_URI),
        "allow_partial_failure": False,
    }
    actual = response.to_dict()
    assert actual == expected


def test__PrepareBatchDataSyncResponse__to_dict():
    model_dict = PrepareBatchDataSyncResponse(
        requests=[
            BatchDataSyncRequest(
                requests=[
                    DataSyncRequest(
                        source_path=S3_URI,
                        destination_path=S3_URI,
                        retain_source_data=True,
                    ),
                ],
            ),
        ],
    )
    expected = {
        "requests": [
            {
                "requests": [
                    {
                        "source_path": str(S3_URI),
                        "destination_path": str(S3_URI),
                        "fail_if_missing": True,
                        "max_concurrency": 25,
                        "require_lock": False,
                        "force": False,
                        "size_only": False,
                        "retain_source_data": True,
                        "include_detailed_response": False,
                        "remote_to_local_config": {"use_custom_tmp_dir": False},
                    },
                ],
                "allow_partial_failure": False,
            },
        ],
    }
    actual = model_dict.to_dict()
    assert actual == expected


def test__PrepareBatchDataSyncResponse__to_dict__s3_paths():
    model_dict = PrepareBatchDataSyncResponse(
        requests=[BatchDataSyncRequest(requests=S3_URI)],
    )
    expected = {
        "requests": [
            {
                "requests": str(S3_URI),
                "allow_partial_failure": False,
            },
        ],
    }
    actual = model_dict.to_dict()
    assert actual == expected


def test__PrepareBatchDataSyncResponse__from_dict():
    expected = PrepareBatchDataSyncResponse(
        requests=[
            BatchDataSyncRequest(
                requests=[
                    DataSyncRequest(
                        source_path=S3_URI,
                        destination_path=S3_URI,
                        retain_source_data=True,
                    ),
                ],
            ),
        ],
    )
    model_dict = {
        "requests": [
            {
                "requests": [
                    {
                        "source_path": str(S3_URI),
                        "destination_path": str(S3_URI),
                        "fail_if_missing": True,
                        "max_concurrency": 25,
                        "require_lock": False,
                        "force": False,
                        "size_only": False,
                        "retain_source_data": True,
                        "remote_to_local_config": {"use_custom_tmp_dir": False},
                    },
                ],
            },
        ],
        "allow_partial_failure": False,
    }
    actual = PrepareBatchDataSyncResponse.from_dict(model_dict)
    assert actual == expected
