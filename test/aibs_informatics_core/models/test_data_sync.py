from pathlib import Path

from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.data_sync import (
    BatchDataSyncRequest,
    BatchDataSyncResponse,
    BatchDataSyncResult,
    DataSyncConfig,
    DataSyncFilterConfig,
    DataSyncRequest,
    DataSyncResult,
    DataSyncTask,
    JSONContent,
    JSONReference,
    PrepareBatchDataSyncResponse,
    RemoteToLocalConfig,
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
                "delete": True,
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
                        "delete": True,
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


def test__BatchDataSyncResponse__add_failed_request():
    # Create a dummy DataSyncRequest
    request = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        retain_source_data=True,
    )

    # Create a BatchDataSyncResponse with an empty BatchDataSyncResult
    response = BatchDataSyncResponse(result=BatchDataSyncResult())

    # Initially, failed_requests should be None
    assert response.failed_requests is None

    # Add the first failed request
    response.add_failed_request(request)

    # Verify that failed_requests is now a list with one element
    assert response.failed_requests is not None
    assert len(response.failed_requests) == 1
    assert response.failed_requests[0] == request

    # Create a second DataSyncRequest with different retain_source_data value
    request2 = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        retain_source_data=False,
    )

    # Add the second failed request
    response.add_failed_request(request2)

    # Verify that both requests are in the failed_requests list
    assert len(response.failed_requests) == 2
    assert response.failed_requests[1] == request2


def test__DataSyncResult__add_bytes_and_files_transferred():
    # Create a DataSyncResult instance with default values
    result = DataSyncResult()

    # Test adding bytes transferred
    result.add_bytes_transferred(1024)
    assert result.bytes_transferred == 1024
    result.add_bytes_transferred(512)
    assert result.bytes_transferred == 1536

    # Test adding files transferred
    result.add_files_transferred(1)
    assert result.files_transferred == 1
    result.add_files_transferred(4)
    assert result.files_transferred == 5


def test__BatchDataSyncResult__increment_counts():
    # Create a BatchDataSyncResult instance with default counts
    result = BatchDataSyncResult()

    # Initially, all counts should be 0
    assert result.total_requests_count == 0
    assert result.successful_requests_count == 0
    assert result.failed_requests_count == 0

    # Increment successful requests count
    result.increment_successful_requests_count(2)
    assert result.successful_requests_count == 2
    assert result.total_requests_count == 2

    # Increment failed requests count
    result.increment_failed_requests_count(3)
    assert result.failed_requests_count == 3
    # Total requests count should now be 2 (from successful) + 3 (from failed) = 5
    assert result.total_requests_count == 5


def test__DataSyncFilterConfig__defaults_to_no_filters():
    config = DataSyncFilterConfig()
    assert config.include is None
    assert config.exclude is None
    assert config.include_patterns is None
    assert config.exclude_patterns is None


def test__DataSyncFilterConfig__compiles_single_pattern():
    config = DataSyncFilterConfig(include=r".*\.bam", exclude=r".*\.bai")
    assert [p.pattern for p in config.include_patterns] == [r".*\.bam"]
    assert [p.pattern for p in config.exclude_patterns] == [r".*\.bai"]


def test__DataSyncFilterConfig__compiles_pattern_list():
    config = DataSyncFilterConfig(include=[r".*\.bam", r".*\.vcf"], exclude=[])
    assert [p.pattern for p in config.include_patterns] == [r".*\.bam", r".*\.vcf"]
    assert config.exclude_patterns is None


def test__DataSyncFilterConfig__round_trip():
    config = DataSyncFilterConfig(include=[r"s1/.*"], exclude=r".*\.bam")
    model_dict = config.to_dict()
    assert model_dict == {"include": [r"s1/.*"], "exclude": r".*\.bam"}
    assert DataSyncFilterConfig.from_dict(model_dict) == config


def test__DataSyncFilterConfig__cached_properties_do_not_leak_into_serialization():
    # cached_property values live on the instance; ensure they stay out of to_dict()
    # and out of equality.
    config = DataSyncFilterConfig(include=r"s1/.*")
    assert config.include_patterns is not None
    assert config.exclude_patterns is None
    assert config.to_dict() == {"include": r"s1/.*"}
    assert config == DataSyncFilterConfig(include=r"s1/.*")


def test__DataSyncTask__round_trip__with_filter_config():
    task = DataSyncTask(
        source_path=S3_URI,
        destination_path=S3_URI,
        filter_config=DataSyncFilterConfig(include=r"s1/.*"),
        filter_root=str(S3_URI),
    )
    model_dict = task.to_dict()
    assert model_dict["filter_config"] == {"include": r"s1/.*"}
    assert model_dict["filter_root"] == str(S3_URI)
    assert DataSyncTask.from_dict(model_dict) == task


def test__DataSyncTask__round_trip__without_filter_config():
    task = DataSyncTask(source_path=S3_URI, destination_path=S3_URI)
    model_dict = task.to_dict()
    assert "filter_config" not in model_dict
    assert "filter_root" not in model_dict
    assert DataSyncTask.from_dict(model_dict) == task


def test__DataSyncRequest__round_trip__with_filter_config():
    request = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        filter_config=DataSyncFilterConfig(include=[r"s1/.*"], exclude=r".*\.bam"),
        filter_root=str(S3_URI),
        delete=False,
    )
    model_dict = request.to_dict()
    assert model_dict["filter_config"] == {"include": [r"s1/.*"], "exclude": r".*\.bam"}
    assert model_dict["delete"] is False
    assert DataSyncRequest.from_dict(model_dict) == request


def test__DataSyncRequest__round_trip__without_filter_config():
    request = DataSyncRequest(source_path=S3_URI, destination_path=S3_URI)
    model_dict = request.to_dict()
    assert "filter_config" not in model_dict
    assert model_dict["delete"] is True
    assert DataSyncRequest.from_dict(model_dict) == request


def test__DataSyncRequest__config_carries_every_config_field():
    # The config property enumerates fields by hand, so new fields are silently dropped
    # unless added. Every field is set to a non-default value to catch that.
    request = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        max_concurrency=1,
        retain_source_data=False,
        delete=False,
        require_lock=True,
        force=True,
        size_only=True,
        fail_if_missing=False,
        include_detailed_response=True,
        remote_to_local_config=RemoteToLocalConfig(use_custom_tmp_dir=True),
    )
    config = request.config
    for field_name in DataSyncConfig.model_fields:
        assert getattr(config, field_name) == getattr(request, field_name), field_name


def test__DataSyncRequest__task_carries_every_task_field():
    request = DataSyncRequest(
        source_path=S3_URI,
        destination_path=S3_URI,
        source_path_prefix=S3KeyPrefix("prefix"),
        filter_config=DataSyncFilterConfig(include=r"s1/.*", exclude=r".*\.bam"),
        filter_root=str(S3_URI),
    )
    task = request.task
    for field_name in DataSyncTask.model_fields:
        assert getattr(task, field_name) == getattr(request, field_name), field_name


def test__BatchDataSyncRequest__from_dict__flattened_request_with_filter_config():
    # A single flattened DataSyncRequest -- including a nested filter_config -- is still
    # recognized by _handle_single_flattened_request and wrapped into a batch.
    single_request = {
        "source_path": str(S3_URI),
        "destination_path": str(S3_URI),
        "filter_config": {"include": [r"s1/.*"], "exclude": r".*\.bam"},
        "filter_root": str(S3_URI),
        "delete": False,
    }
    actual = BatchDataSyncRequest.from_dict(single_request)
    assert actual.requests == [DataSyncRequest.from_dict(single_request)]
    assert actual.requests[0].filter_config == DataSyncFilterConfig(
        include=[r"s1/.*"], exclude=r".*\.bam"
    )
    assert actual.requests[0].filter_root == str(S3_URI)
    assert actual.requests[0].delete is False


def test__BatchDataSyncRequest__round_trip__with_filter_config():
    # This is the seam the SFN Map state crosses -- filters must survive it.
    request = BatchDataSyncRequest(
        requests=[
            DataSyncRequest(
                source_path=S3_URI,
                destination_path=S3_URI,
                filter_config=DataSyncFilterConfig(include=r"s1/.*"),
                filter_root=str(S3_URI),
                delete=False,
            ),
        ],
    )
    assert BatchDataSyncRequest.from_dict(request.to_dict()) == request


def test__PrepareBatchDataSyncResponse__round_trip__with_filter_config():
    response = PrepareBatchDataSyncResponse(
        requests=[
            BatchDataSyncRequest(
                requests=[
                    DataSyncRequest(
                        source_path=S3_URI,
                        destination_path=S3_URI,
                        filter_config=DataSyncFilterConfig(
                            include=[r"s1/.*"], exclude=[r".*\.bam"]
                        ),
                        filter_root=str(S3_URI),
                        delete=False,
                    ),
                ],
            ),
        ],
    )
    assert PrepareBatchDataSyncResponse.from_dict(response.to_dict()) == response
