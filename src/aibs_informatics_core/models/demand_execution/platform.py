from aibs_informatics_core.models.aws.iam import IAMRoleArn
from aibs_informatics_core.models.base import PydanticBaseModel


class AWSBatchExecutionPlatform(PydanticBaseModel):
    job_queue_name: str
    job_role: IAMRoleArn | str | None = None


# TODO: I would prefer to make ExecutionPlatform polymorphic, but datacalasses does not support it
#       For now, I will just make a
class ExecutionPlatform(PydanticBaseModel):
    aws_batch: AWSBatchExecutionPlatform | None = None
