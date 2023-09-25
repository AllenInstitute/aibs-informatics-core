from pathlib import Path
from test.base import BaseTest, does_not_raise
from typing import List, Optional
from unittest import mock

from pytest import mark, param, raises

from aibs_informatics_core.env import EnvBase
from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.data_sync import (
    BatchDataSyncRequest,
    BatchDataSyncResponse,
    DataSyncConfig,
    DataSyncRequest,
    DataSyncResponse,
    DataSyncTask,
    GetJSONFromFileRequest,
    GetJSONFromFileResponse,
    JSONContent,
    JSONReference,
    PrepareBatchDataSyncRequest,
    PrepareBatchDataSyncResponse,
    PutJSONToFileRequest,
    PutJSONToFileResponse,
)

S3_URI = S3URI.build(bucket_name="bucket", key="key")
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
    assert request.config == request
    assert request.task == request


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
                source_path_prefix="prefix",
            ),
        ],
    )
    actual = BatchDataSyncRequest.from_dict(model_dict)
    assert actual == expected

    # handles single request
    actual = BatchDataSyncRequest.from_dict(single_request)
    assert actual == expected
