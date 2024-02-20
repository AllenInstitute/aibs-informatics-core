from dataclasses import dataclass
from typing import Any, List, Optional, cast

from aibs_informatics_core.models.base import SchemaModel, StringField, custom_field


@dataclass
class AWSBatchExecutionPlatform(SchemaModel):
    job_queue_name: str


# TODO: I would prefer to make ExecutionPlatform polymorphic, but datacalasses does not support it
#       For now, I will just make a
@dataclass
class ExecutionPlatform(SchemaModel):
    aws_batch: Optional[AWSBatchExecutionPlatform] = custom_field(
        mm_field=AWSBatchExecutionPlatform.as_mm_field(), default=None
    )
