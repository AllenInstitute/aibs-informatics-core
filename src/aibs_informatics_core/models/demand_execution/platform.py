from aibs_informatics_core.models.aws.iam import IAMRoleArn
from aibs_informatics_core.models.base import PydanticBaseModel, custom_field
from aibs_informatics_core.models.base.custom_fields import (
    CustomStringField,
    StringField,
    UnionField,
)


class AWSBatchExecutionPlatform(PydanticBaseModel):
    job_queue_name: str
    job_role: str | IAMRoleArn | None = custom_field(
        mm_field=UnionField([(IAMRoleArn, CustomStringField(IAMRoleArn)), (str, StringField())]),
        default=None,
    )


# TODO: I would prefer to make ExecutionPlatform polymorphic, but datacalasses does not support it
#       For now, I will just make a
class ExecutionPlatform(PydanticBaseModel):
    aws_batch: AWSBatchExecutionPlatform | None = custom_field(
        mm_field=AWSBatchExecutionPlatform.as_mm_field(), default=None
    )
