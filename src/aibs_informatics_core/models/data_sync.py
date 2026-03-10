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

from pydantic import Field, JsonValue, model_validator

from aibs_informatics_core.models.aws.efs import EFSPath
from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.base import PydanticBaseModel
from aibs_informatics_core.utils.json import JSON


class JSONContent(PydanticBaseModel):
    content: JsonValue


class JSONReference(PydanticBaseModel):
    path: S3Path | Path


class PutJSONToFileRequest(JSONContent):
    path: S3Path | Path | None = None


class PutJSONToFileResponse(JSONReference):
    pass


class GetJSONFromFileRequest(JSONReference):
    pass


class GetJSONFromFileResponse(JSONContent):
    pass


class DataSyncTask(PydanticBaseModel):
    source_path: S3Path | EFSPath | Path
    destination_path: S3Path | EFSPath | Path
    source_path_prefix: S3KeyPrefix | None = None


class RemoteToLocalConfig(PydanticBaseModel):
    # Use a custom intermediate tmp dir when syncing an s3 object to a local filesystem
    # instead of using boto3's implementation which creates a part file (e.g. *.6eF5b5da)
    # in SAME parent dir as the desired destination path.
    use_custom_tmp_dir: bool = False
    custom_tmp_dir: EFSPath | Path | None = None


class DataSyncConfig(PydanticBaseModel):
    max_concurrency: int = 25
    retain_source_data: bool = True
    require_lock: bool = False
    force: bool = False
    size_only: bool = False
    fail_if_missing: bool = True
    include_detailed_response: bool = False
    remote_to_local_config: RemoteToLocalConfig = Field(default_factory=RemoteToLocalConfig)


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
    request: DataSyncRequest
    result: DataSyncResult


class BatchDataSyncRequest(PydanticBaseModel):
    requests: list[DataSyncRequest] | S3Path
    allow_partial_failure: bool = False

    @model_validator(mode="before")
    @classmethod
    def _handle_single_flattened_request(cls, data: dict[str, JSON]) -> dict[str, JSON]:
        if DataSyncRequest.is_valid(data=data):
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
    result: BatchDataSyncResult
    failed_requests: list[DataSyncRequest] | None = None

    def add_failed_request(self, request: DataSyncRequest) -> None:
        if self.failed_requests is None:
            self.failed_requests = []
        self.failed_requests.append(request)


class PrepareBatchDataSyncRequest(DataSyncRequest):
    batch_size_bytes_limit: int | None = None
    temporary_request_payload_path: S3Path | None = None


class PrepareBatchDataSyncResponse(PydanticBaseModel):
    requests: list[BatchDataSyncRequest]
