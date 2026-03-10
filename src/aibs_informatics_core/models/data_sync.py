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
    """Model containing raw JSON content."""

    content: JsonValue


class JSONReference(PydanticBaseModel):
    """Model containing a reference to a JSON file."""

    path: S3Path | Path


class PutJSONToFileRequest(JSONContent):
    """Request to write JSON content to a file."""

    path: S3Path | Path | None = None


class PutJSONToFileResponse(JSONReference):
    """Response from writing JSON content to a file."""

    pass


class GetJSONFromFileRequest(JSONReference):
    """Request to read JSON content from a file."""

    pass


class GetJSONFromFileResponse(JSONContent):
    """Response containing JSON content read from a file."""

    pass


class DataSyncTask(PydanticBaseModel):
    """Defines source and destination paths for a data sync operation."""

    source_path: S3Path | EFSPath | Path
    destination_path: S3Path | EFSPath | Path
    source_path_prefix: S3KeyPrefix | None = None


class RemoteToLocalConfig(PydanticBaseModel):
    """Configuration for syncing remote data to local filesystem."""

    # Use a custom intermediate tmp dir when syncing an s3 object to a local filesystem
    # instead of using boto3's implementation which creates a part file (e.g. *.6eF5b5da)
    # in SAME parent dir as the desired destination path.
    use_custom_tmp_dir: bool = False
    custom_tmp_dir: EFSPath | Path | None = None


class DataSyncConfig(PydanticBaseModel):
    """Configuration options for data sync operations."""

    max_concurrency: int = 25
    retain_source_data: bool = True
    require_lock: bool = False
    force: bool = False
    size_only: bool = False
    fail_if_missing: bool = True
    include_detailed_response: bool = False
    remote_to_local_config: RemoteToLocalConfig = Field(default_factory=RemoteToLocalConfig)


class DataSyncRequest(DataSyncConfig, DataSyncTask):  # type: ignore[misc]
    """Combined request model for a single data sync operation."""

    @property
    def config(self) -> DataSyncConfig:
        """Extract the configuration portion of this request."""
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
        """Extract the task portion of this request."""
        return DataSyncTask(
            source_path=self.source_path,
            destination_path=self.destination_path,
            source_path_prefix=self.source_path_prefix,
        )


class DataSyncResult(PydanticBaseModel):
    """Result metrics for a data sync operation."""

    bytes_transferred: int = 0
    files_transferred: int = 0

    def add_bytes_transferred(self, bytes_transferred: int) -> None:
        """Increment the bytes transferred counter."""
        self.bytes_transferred += bytes_transferred

    def add_files_transferred(self, files_transferred: int) -> None:
        """Increment the files transferred counter."""
        self.files_transferred += files_transferred


class DataSyncResponse(PydanticBaseModel):
    """Response from a single data sync operation."""

    request: DataSyncRequest
    result: DataSyncResult


class BatchDataSyncRequest(PydanticBaseModel):
    """Request for a batch of data sync operations."""

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
    """Aggregated result metrics for a batch data sync."""

    total_requests_count: int = 0
    successful_requests_count: int = 0
    failed_requests_count: int = 0

    def increment_successful_requests_count(self, increment: int = 1) -> None:
        """Increment the successful and total request counters."""
        self.successful_requests_count += increment
        self.total_requests_count += increment

    def increment_failed_requests_count(self, increment: int = 1) -> None:
        """Increment the failed and total request counters."""
        self.failed_requests_count += increment
        self.total_requests_count += increment


class BatchDataSyncResponse(PydanticBaseModel):
    """Response from a batch data sync operation."""

    result: BatchDataSyncResult
    failed_requests: list[DataSyncRequest] | None = None

    def add_failed_request(self, request: DataSyncRequest) -> None:
        """Add a request to the list of failed requests."""
        if self.failed_requests is None:
            self.failed_requests = []
        self.failed_requests.append(request)


class PrepareBatchDataSyncRequest(DataSyncRequest):
    """Request to prepare a batch of data sync operations from a single sync task."""

    batch_size_bytes_limit: int | None = None
    temporary_request_payload_path: S3Path | None = None


class PrepareBatchDataSyncResponse(PydanticBaseModel):
    """Response containing prepared batch data sync requests."""

    requests: list[BatchDataSyncRequest]
