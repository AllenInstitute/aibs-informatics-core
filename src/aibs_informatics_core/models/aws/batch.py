import re

from pydantic import Field

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.base import PydanticBaseModel


class JobName(ValidatedStr):
    regex_pattern = re.compile(r"([a-zA-Z0-9][\w_-]{0,127})")


class ResourceRequirements(PydanticBaseModel):
    GPU: int | None = None
    MEMORY: int | None = None
    VCPU: int | None = None


class KeyValuePairType(PydanticBaseModel):
    Name: str
    Value: str


class ContainerDetail(PydanticBaseModel):
    Image: str
    Environment: list[KeyValuePairType]
    ContainerInstanceArn: str
    TaskArn: str


class AttemptContainerDetail(PydanticBaseModel):
    ContainerInstanceArn: str | None = None
    TaskArn: str | None = None
    ExitCode: int | None = None
    Reason: str | None = None
    LogStreamName: str | None = None


class AttemptDetail(PydanticBaseModel):
    Container: AttemptContainerDetail | None = None
    StartedAt: int | None = None
    StoppedAt: int | None = None
    StatusReason: str | None = None

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
    JobName: str
    JobId: str
    JobQueue: str
    Status: str
    StartedAt: int
    JobDefinition: str

    # Optional
    JobArn: str | None = Field(default=None, repr=False)
    StatusReason: str | None = Field(default=None, repr=False)
    Attempts: list[AttemptDetail] = Field(default_factory=list, repr=False)
    Container: ContainerDetail | None = Field(default=None, repr=False)
    Parameters: dict[str, str] = Field(default_factory=dict, repr=False)
    CreatedAt: int | None = Field(default=None, repr=False)
    StoppedAt: int | None = Field(default=None, repr=False)
    IsCancelled: bool | None = Field(default=None, repr=False)
    IsTerminated: bool | None = Field(default=None, repr=False)

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
