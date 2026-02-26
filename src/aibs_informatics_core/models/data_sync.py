__all__ = [
    "JSONContent",
    "JSONReference",
    "PutJSONToFileRequest",
    "PutJSONToFileResponse",
    "GetJSONFromFileRequest",
    "GetJSONFromFileResponse",
    "DataSyncTask",
    "DataSyncConfig",
    "DataSyncRequest",
    "DataSyncResponse",
    "BatchDataSyncRequest",
    "BatchDataSyncResponse",
    "PrepareBatchDataSyncRequest",
    "PrepareBatchDataSyncResponse",
]

from pathlib import Path
from typing import Any

from pydantic import model_validator

from aibs_informatics_core.models.aws.efs import EFSPath
from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.base import (
    BooleanField,
    CustomStringField,
    IntegerField,
    ListField,
    PathField,
    RawField,
    PydanticBaseModel,
    UnionField,
    custom_field,
)
from aibs_informatics_core.utils.json import JSON


class JSONContent(PydanticBaseModel):
    content: JSON = custom_field(mm_field=RawField())


class JSONReference(PydanticBaseModel):
    path: S3Path | Path = custom_field(
        mm_field=UnionField([(S3Path, S3Path.as_mm_field()), (Path, PathField())])
    )


class PutJSONToFileRequest(JSONContent):
    path: S3Path | Path | None = custom_field(
        default=None, mm_field=UnionField([(S3Path, S3Path.as_mm_field()), (Path, PathField())])
    )


class PutJSONToFileResponse(JSONReference):
    pass


class GetJSONFromFileRequest(JSONReference):
    pass


class GetJSONFromFileResponse(JSONContent):
    pass


class DataSyncTask(PydanticBaseModel):
    source_path: S3Path | EFSPath | Path = custom_field(
        mm_field=UnionField(
            [
                (S3Path, S3Path.as_mm_field()),
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        )
    )
    destination_path: S3Path | EFSPath | Path = custom_field(
        mm_field=UnionField(
            [
                (S3Path, S3Path.as_mm_field()),
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        )
    )
    source_path_prefix: S3KeyPrefix | None = custom_field(
        default=None, mm_field=CustomStringField(S3KeyPrefix)
    )


class RemoteToLocalConfig(PydanticBaseModel):
    # Use a custom intermediate tmp dir when syncing an s3 object to a local filesystem
    # instead of using boto3's implementation which creates a part file (e.g. *.6eF5b5da)
    # in SAME parent dir as the desired destination path.
    use_custom_tmp_dir: bool = custom_field(default=False, mm_field=BooleanField())
    custom_tmp_dir: EFSPath | Path | None = custom_field(
        default=None,
        mm_field=UnionField(
            [
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        ),
    )


class DataSyncConfig(PydanticBaseModel):
    max_concurrency: int = custom_field(default=25, mm_field=IntegerField())
    retain_source_data: bool = custom_field(default=True, mm_field=BooleanField())
    require_lock: bool = custom_field(default=False, mm_field=BooleanField())
    force: bool = custom_field(default=False, mm_field=BooleanField())
    size_only: bool = custom_field(default=False, mm_field=BooleanField())
    fail_if_missing: bool = custom_field(default=True, mm_field=BooleanField())
    include_detailed_response: bool = custom_field(default=False, mm_field=BooleanField())
    remote_to_local_config: RemoteToLocalConfig = custom_field(
        default_factory=RemoteToLocalConfig,
        mm_field=RemoteToLocalConfig.as_mm_field(),
    )


class DataSyncRequest(DataSyncConfig, DataSyncTask):  # type: ignore[misc]
    @property
    def config(self) -> DataSyncConfig:
        return DataSyncConfig(
            max_concurrency=self.max_concurrency,
            retain_source_data=self.retain_source_data,
            require_lock=self.require_lock,
            force=self.force,
            size_only=self.size_only,
            fail_if_missing=self.fail_if_missing,
            include_detailed_response=self.include_detailed_response,
            remote_to_local_config=self.remote_to_local_config,
        )

    @property
    def task(self) -> DataSyncTask:
        return DataSyncTask(
            source_path=self.source_path,
            destination_path=self.destination_path,
            source_path_prefix=self.source_path_prefix,
        )


class DataSyncResult(PydanticBaseModel):
    bytes_transferred: int = 0
    files_transferred: int = 0

    def add_bytes_transferred(self, bytes_transferred: int) -> None:
        self.bytes_transferred += bytes_transferred

    def add_files_transferred(self, files_transferred: int) -> None:
        self.files_transferred += files_transferred


class DataSyncResponse(PydanticBaseModel):
    request: DataSyncRequest = custom_field(mm_field=DataSyncRequest.as_mm_field())
    result: DataSyncResult = custom_field(mm_field=DataSyncResult.as_mm_field())


class BatchDataSyncRequest(PydanticBaseModel):
    requests: list[DataSyncRequest] | S3Path = custom_field(
        mm_field=UnionField(
            [
                (list, ListField(DataSyncRequest.as_mm_field())),
                (S3Path, S3Path.as_mm_field()),
            ]
        )
    )
    allow_partial_failure: bool = custom_field(default=False, mm_field=BooleanField())

    @model_validator(mode="before")
    @classmethod
    def _handle_single_flattened_request(cls, data: dict[str, Any]) -> dict[str, Any]:
        if DataSyncRequest.is_valid(data=data, many=False):
            data = {
                "requests": [data],
                "allow_partial_failure": False,
                "include_detailed_response": False,
            }
        return data


class BatchDataSyncResult(DataSyncResult):
    total_requests_count: int = 0
    successful_requests_count: int = 0
    failed_requests_count: int = 0

    def increment_successful_requests_count(self, increment: int = 1) -> None:
        self.successful_requests_count += increment
        self.total_requests_count += increment

    def increment_failed_requests_count(self, increment: int = 1) -> None:
        self.failed_requests_count += increment
        self.total_requests_count += increment


class BatchDataSyncResponse(PydanticBaseModel):
    result: BatchDataSyncResult = custom_field(mm_field=BatchDataSyncResult.as_mm_field())
    failed_requests: list[DataSyncRequest] | None = custom_field(default=None)

    def add_failed_request(self, request: DataSyncRequest) -> None:
        if self.failed_requests is None:
            self.failed_requests = []
        self.failed_requests.append(request)


class PrepareBatchDataSyncRequest(DataSyncRequest):
    batch_size_bytes_limit: int | None = custom_field(default=None, mm_field=IntegerField())
    temporary_request_payload_path: S3Path | None = custom_field(
        default=None, mm_field=S3Path.as_mm_field()
    )


class PrepareBatchDataSyncResponse(PydanticBaseModel):
    requests: list[BatchDataSyncRequest] = custom_field(
        mm_field=ListField(BatchDataSyncRequest.as_mm_field())
    )
