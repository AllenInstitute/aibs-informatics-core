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

import marshmallow as mm

from aibs_informatics_core.models.aws.efs import EFSPath
from aibs_informatics_core.models.aws.s3 import S3KeyPrefix, S3Path
from aibs_informatics_core.models.base import (
    BooleanField,
    CustomStringField,
    IntegerField,
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
class DataSyncConfig(SchemaModel):
    max_concurrency: int = custom_field(default=25, mm_field=IntegerField())
    retain_source_data: bool = custom_field(default=True, mm_field=BooleanField())
    require_lock: bool = custom_field(default=False, mm_field=BooleanField())


@dataclass
class DataSyncRequest(DataSyncConfig, DataSyncTask):  # type: ignore[misc]
    @property
    def config(self) -> DataSyncConfig:
        return self

    @property
    def task(self) -> DataSyncTask:
        return self


@dataclass
class DataSyncResponse(SchemaModel):
    request: DataSyncRequest


@dataclass
class BatchDataSyncRequest(SchemaModel):
    requests: List[DataSyncRequest]

    @classmethod
    @mm.pre_load
    def _handle_single_flattened_request(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if DataSyncRequest.is_valid(data=data, many=False, partial=False):
            data = {"requests": [data]}
        return data


@dataclass
class BatchDataSyncResponse(SchemaModel):
    responses: List[DataSyncResponse]


@dataclass
class PrepareBatchDataSyncRequest(DataSyncRequest):
    batch_size_bytes_limit: Optional[int] = custom_field(default=None, mm_field=IntegerField())


@dataclass
class PrepareBatchDataSyncResponse(SchemaModel):
    requests: List[BatchDataSyncRequest]
