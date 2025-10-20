from dataclasses import dataclass
from typing import Optional, Union

from aibs_informatics_core.models.aws.iam import IAMRoleArn
from aibs_informatics_core.models.base import SchemaModel, custom_field
from aibs_informatics_core.models.base.custom_fields import (
    CustomStringField,
    StringField,
    UnionField,
)


@dataclass
class AWSBatchExecutionPlatform(SchemaModel):
    job_queue_name: str
    job_role: Optional[Union[str, IAMRoleArn]] = custom_field(
        mm_field=UnionField([(IAMRoleArn, CustomStringField(IAMRoleArn)), (str, StringField())]),
        default=None,
    )


# TODO: I would prefer to make ExecutionPlatform polymorphic, but datacalasses does not support it
#       For now, I will just make a
@dataclass
class ExecutionPlatform(SchemaModel):
    aws_batch: Optional[AWSBatchExecutionPlatform] = custom_field(
        mm_field=AWSBatchExecutionPlatform.as_mm_field(), default=None
    )
