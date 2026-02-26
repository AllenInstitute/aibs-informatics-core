import re

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.base import IntegerField, ListField, PydanticBaseModel, custom_field


class JobName(ValidatedStr):
    regex_pattern = re.compile(r"([a-zA-Z0-9][\w_-]{0,127})")


class ResourceRequirements(PydanticBaseModel):
    GPU: int | None = custom_field(mm_field=IntegerField(strict=False), default=None)
    MEMORY: int | None = custom_field(mm_field=IntegerField(strict=False), default=None)
    VCPU: int | None = custom_field(mm_field=IntegerField(strict=False), default=None)


class KeyValuePairType(PydanticBaseModel):
    Name: str
    Value: str


class ContainerDetail(PydanticBaseModel):
    Image: str = custom_field()
    Environment: list[KeyValuePairType] = custom_field(
        mm_field=ListField(KeyValuePairType.as_mm_field())
    )
    ContainerInstanceArn: str = custom_field()
    TaskArn: str = custom_field()


class AttemptContainerDetail(PydanticBaseModel):
    ContainerInstanceArn: str | None = custom_field(default=None)
    TaskArn: str | None = custom_field(default=None)
    ExitCode: int | None = custom_field(default=None)
    Reason: str | None = custom_field(default=None)
    LogStreamName: str | None = custom_field(default=None)


class AttemptDetail(PydanticBaseModel):
    Container: AttemptContainerDetail | None = custom_field(
        mm_field=AttemptContainerDetail.as_mm_field(), default=None
    )
    StartedAt: int | None = custom_field(default=None)
    StoppedAt: int | None = custom_field(default=None)
    StatusReason: str | None = custom_field(default=None)

    @property
    def duration(self) -> int | None:
        if self.StoppedAt and self.StartedAt:
            return self.StoppedAt - self.StartedAt
        return None

    @property
    def container_instance_arn(self) -> str | None:
        if self.Container:
            return self.Container.ContainerInstanceArn
        return None

    @property
    def container_task_arn(self) -> str | None:
        if self.Container:
            return self.Container.TaskArn
        return None


class BatchJobDetail(PydanticBaseModel):
    JobName: str = custom_field()
    JobId: str = custom_field()
    JobQueue: str = custom_field()
    Status: str = custom_field()
    StartedAt: int = custom_field()
    JobDefinition: str = custom_field()

    # Optional
    JobArn: str | None = custom_field(default=None, repr=False)
    StatusReason: str | None = custom_field(default=None, repr=False)
    Attempts: list[AttemptDetail] = custom_field(
        mm_field=ListField(AttemptDetail.as_mm_field()), default_factory=list, repr=False
    )
    Container: ContainerDetail | None = custom_field(
        mm_field=ContainerDetail.as_mm_field(), default=None, repr=False
    )
    Parameters: dict[str, str] = custom_field(default_factory=dict, repr=False)
    CreatedAt: int | None = custom_field(default=None, repr=False)
    StoppedAt: int | None = custom_field(default=None, repr=False)
    IsCancelled: bool | None = custom_field(default=None, repr=False)
    IsTerminated: bool | None = custom_field(default=None, repr=False)

    @property
    def duration(self) -> int | None:
        if self.StoppedAt and self.StartedAt:
            return self.StoppedAt - self.StartedAt
        return None

    @property
    def container_name_and_tag(self) -> tuple[str, str | None]:
        if self.Container:
            (container, container_tag) = self.Container.Image.split(":", maxsplit=1)
            return (container, container_tag)
        return ("NotAvailable", None)

    @property
    def container_tag(self) -> str | None:
        return self.container_name_and_tag[1]

    @property
    def container_environment(self) -> dict[str, str]:
        return {
            env_var.Name: env_var.Value
            for env_var in (self.Container.Environment if self.Container else {})
        }

    @property
    def container_instance_arn(self) -> str | None:
        if self.Container:
            return self.Container.ContainerInstanceArn
        return None

    @property
    def container_instance_arns(self) -> list[str]:
        return [
            _
            for _ in {
                self.container_instance_arn,
                *[a.Container.ContainerInstanceArn for a in self.Attempts or [] if a.Container],
            }
            if _ is not None
        ]

    @property
    def container_task_arn(self) -> str | None:
        if self.Container:
            return self.Container.TaskArn
        return None
