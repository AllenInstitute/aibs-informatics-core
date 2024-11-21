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

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib import request

import marshmallow as mm

from aibs_informatics_core.models.aws.efs import EFSPath
from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.base import (
    BooleanField,
    CustomStringField,
    IntegerField,
    ListField,
    PathField,
    RawField,
    SchemaModel,
    UnionField,
    custom_field,
)
from aibs_informatics_core.utils.json import JSON


@dataclass
class JSONContent(SchemaModel):
    content: JSON = custom_field(mm_field=RawField())


@dataclass
class JSONReference(SchemaModel):
    path: Union[S3Path, Path] = custom_field(
        mm_field=UnionField([(S3Path, S3Path.as_mm_field()), (Path, PathField())])
    )


@dataclass
class PutJSONToFileRequest(JSONContent):
    path: Optional[Union[S3Path, Path]] = custom_field(
        default=None, mm_field=UnionField([(S3Path, S3Path.as_mm_field()), (Path, PathField())])
    )


@dataclass
class PutJSONToFileResponse(JSONReference):
    pass


@dataclass
class GetJSONFromFileRequest(JSONReference):
    pass


@dataclass
class GetJSONFromFileResponse(JSONContent):
    pass


@dataclass
class DataSyncTask(SchemaModel):
    source_path: Union[S3Path, EFSPath, Path] = custom_field(
        mm_field=UnionField(
            [
                (S3Path, S3Path.as_mm_field()),
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        )
    )
    destination_path: Union[S3Path, EFSPath, Path] = custom_field(
        mm_field=UnionField(
            [
                (S3Path, S3Path.as_mm_field()),
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        )
    )
    source_path_prefix: Optional[S3KeyPrefix] = custom_field(
        default=None, mm_field=CustomStringField(S3KeyPrefix)
    )


@dataclass
class RemoteToLocalConfig(SchemaModel):
    # Use a custom intermediate tmp dir when syncing an s3 object to a local filesystem
    # instead of using boto3's implementation which creates a part file (e.g. *.6eF5b5da)
    # in SAME parent dir as the desired destination path.
    use_custom_tmp_dir: bool = custom_field(default=False, mm_field=BooleanField())
    custom_tmp_dir: Optional[Union[EFSPath, Path]] = custom_field(
        default=None,
        mm_field=UnionField(
            [
                (EFSPath, EFSPath.as_mm_field()),
                ((Path, str), PathField()),
            ]
        ),
    )


@dataclass
class DataSyncConfig(SchemaModel):
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


@dataclass
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


@dataclass
class DataSyncResult(SchemaModel):
    bytes_transferred: int = 0
    files_transferred: int = 0

    def add_bytes_transferred(self, bytes_transferred: int) -> None:
        self.bytes_transferred += bytes_transferred

    def add_files_transferred(self, files_transferred: int) -> None:
        self.files_transferred += files_transferred


@dataclass
class DataSyncResponse(SchemaModel):
    request: DataSyncRequest = custom_field(mm_field=DataSyncRequest.as_mm_field())
    result: DataSyncResult = custom_field(mm_field=DataSyncResult.as_mm_field())


@dataclass
class BatchDataSyncRequest(SchemaModel):
    requests: Union[List[DataSyncRequest], S3Path] = custom_field(
        mm_field=UnionField(
            [
                (list, ListField(DataSyncRequest.as_mm_field())),
                (S3Path, S3Path.as_mm_field()),
            ]
        )
    )
    allow_partial_failure: bool = custom_field(default=False, mm_field=BooleanField())

    @classmethod
    @mm.pre_load
    def _handle_single_flattened_request(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if DataSyncRequest.is_valid(data=data, many=False, partial=False):
            data = {
                "requests": [data],
                "allow_partial_failure": False,
                "include_detailed_response": False,
            }
        return data


@dataclass
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


@dataclass
class BatchDataSyncResponse(SchemaModel):
    result: BatchDataSyncResult = custom_field(mm_field=BatchDataSyncResult.as_mm_field())
    failed_requests: Optional[List[DataSyncRequest]] = custom_field(default=None)

    def add_failed_request(self, request: DataSyncRequest) -> None:
        if self.failed_requests is None:
            self.failed_requests = []
        self.failed_requests.append(request)


@dataclass
class PrepareBatchDataSyncRequest(DataSyncRequest):
    batch_size_bytes_limit: Optional[int] = custom_field(default=None, mm_field=IntegerField())
    temporary_request_payload_path: Optional[S3Path] = custom_field(
        default=None, mm_field=S3Path.as_mm_field()
    )


@dataclass
class PrepareBatchDataSyncResponse(SchemaModel):
    requests: List[BatchDataSyncRequest] = custom_field(
        mm_field=ListField(BatchDataSyncRequest.as_mm_field())
    )
