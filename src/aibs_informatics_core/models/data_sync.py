__all__ = [
    "JSONContent",
    "JSONReference",
    "PutJSONToFileRequest",
    "PutJSONToFileResponse",
    "GetJSONFromFileRequest",
    "GetJSONFromFileResponse",
    "DataSyncFilterConfig",
    "DataSyncTask",
    "DataSyncConfig",
    "DataSyncRequest",
    "DataSyncResponse",
    "BatchDataSyncRequest",
    "BatchDataSyncResponse",
    "PrepareBatchDataSyncRequest",
    "PrepareBatchDataSyncResponse",
]

from functools import cached_property
from pathlib import Path
from re import Pattern

from pydantic import Field, JsonValue, model_validator

from aibs_informatics_core.models.aws.efs import EFSPath
from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.base import PydanticBaseModel
from aibs_informatics_core.utils.filters import compile_patterns
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


class DataSyncFilterConfig(PydanticBaseModel):
    """Include/exclude filters restricting which files a data sync moves.

    Patterns follow the shared contract in
    :mod:`aibs_informatics_core.utils.filters`: they are regular expressions
    (not globs) matched with ``fullmatch`` against the path *relative to* the
    filter root, and exclude patterns take precedence over include patterns.
    An absent or empty ``include`` includes everything.

    Attributes:
        include: Optional regex pattern(s) for files to include.
            If multiple patterns, includes files matching any pattern.
        exclude: Optional regex pattern(s) for files to exclude.
            Exclude patterns take precedence over include patterns.
    """

    include: str | list[str] | None = None
    exclude: str | list[str] | None = None

    @cached_property
    def include_patterns(self) -> list[Pattern] | None:
        return compile_patterns(self.include)

    @cached_property
    def exclude_patterns(self) -> list[Pattern] | None:
        return compile_patterns(self.exclude)


class DataSyncTask(PydanticBaseModel):
    """Defines source and destination paths for a data sync operation.

    Attributes:
        source_path: Path to sync data from.
        destination_path: Path to sync data to.
        source_path_prefix: Optional S3 key prefix scoping the source.
        filter_config: Optional include/exclude filters describing *what* to
            move. Filters live on the task rather than the config because they
            change the set of data transferred, not how the transfer runs.
        filter_root: Root that filter patterns are matched relative to.
            **Internal plumbing -- set by the prepare handler, never by users.**
            The distributed sync workflow splits a sync of ``s3://b/run1/`` into
            sub-requests rooted at ``s3://b/run1/sampleA/``. Each sub-request
            re-lists from its own root, so patterns written against ``run1/``
            would silently stop matching. Sub-requests therefore carry the
            original root here. Defaults to the source path when unset.
    """

    source_path: S3Path | EFSPath | Path
    destination_path: S3Path | EFSPath | Path
    source_path_prefix: S3KeyPrefix | None = None
    filter_config: DataSyncFilterConfig | None = None
    filter_root: str | None = None


class RemoteToLocalConfig(PydanticBaseModel):
    """Configuration for syncing remote data to local filesystem."""

    # Use a custom intermediate tmp dir when syncing an s3 object to a local filesystem
    # instead of using boto3's implementation which creates a part file (e.g. *.6eF5b5da)
    # in SAME parent dir as the desired destination path.
    use_custom_tmp_dir: bool = False
    custom_tmp_dir: EFSPath | Path | None = None


class DataSyncConfig(PydanticBaseModel):
    """Configuration options for data sync operations.

    Attributes:
        max_concurrency: Maximum number of concurrent transfer operations.
        retain_source_data: Whether to keep the source data after syncing.
        delete: Whether the sync deletes destination paths that are not present
            in the (filtered) source -- i.e. whether the destination is made to
            *mirror* the source rather than merely receive from it.

            .. warning::
                **This interacts destructively with**
                :class:`DataSyncFilterConfig`. Filters narrow what the sync
                considers to be "the source", so with ``delete=True`` any file
                already at the destination that the filters exclude is treated
                as unexpected and **deleted**. Syncing a filtered subset into a
                directory that holds an earlier unfiltered copy will therefore
                remove the non-matching files.

                This is deliberately *not* guarded by validation -- ``delete``
                is the gate, and mirroring remains a legitimate use of a
                filtered sync. Callers that pass a ``filter_config`` are
                expected to pass ``delete=False`` unless they specifically want
                the destination mirrored to the filtered subset.
        require_lock: Whether to acquire a lock on the destination path.
        force: Whether to transfer regardless of existing destination content.
        size_only: Whether to compare only file sizes when deciding to transfer.
        fail_if_missing: Whether to raise if the source path does not exist.
        include_detailed_response: Whether to compute detailed transfer metrics.
        remote_to_local_config: Options specific to remote-to-local syncs.
    """

    max_concurrency: int = 25
    retain_source_data: bool = True
    delete: bool = True
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
        """Extract the configuration portion of this request.

        Note:
            Fields are enumerated by hand -- any field added to
            :class:`DataSyncConfig` must be added here too, or it will be
            silently dropped.
        """
        return DataSyncConfig(
            max_concurrency=self.max_concurrency,
            retain_source_data=self.retain_source_data,
            delete=self.delete,
            require_lock=self.require_lock,
            force=self.force,
            size_only=self.size_only,
            fail_if_missing=self.fail_if_missing,
            include_detailed_response=self.include_detailed_response,
            remote_to_local_config=self.remote_to_local_config,
        )

    @property
    def task(self) -> DataSyncTask:
        """Extract the task portion of this request.

        Note:
            Fields are enumerated by hand -- any field added to
            :class:`DataSyncTask` must be added here too, or it will be
            silently dropped.
        """
        return DataSyncTask(
            source_path=self.source_path,
            destination_path=self.destination_path,
            source_path_prefix=self.source_path_prefix,
            filter_config=self.filter_config,
            filter_root=self.filter_root,
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
