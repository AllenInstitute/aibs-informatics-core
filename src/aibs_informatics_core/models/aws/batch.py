import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.base import IntegerField, ListField, SchemaModel, custom_field


class JobName(ValidatedStr):
    regex_pattern = re.compile(r"([a-zA-Z0-9][\w_-]*){1-128}")


@dataclass
class ResourceRequirements(SchemaModel):
    GPU: Optional[int] = custom_field(mm_field=IntegerField(strict=False), default=None)
    MEMORY: Optional[int] = custom_field(mm_field=IntegerField(strict=False), default=None)
    VCPU: Optional[int] = custom_field(mm_field=IntegerField(strict=False), default=None)


@dataclass
class KeyValuePairType(SchemaModel):
    Name: str
    Value: str


@dataclass
class ContainerDetail(SchemaModel):
    Image: str = custom_field()
    Environment: List[KeyValuePairType] = custom_field(
        mm_field=ListField(KeyValuePairType.as_mm_field())
    )
    ContainerInstanceArn: str = custom_field()
    TaskArn: str = custom_field()


@dataclass
class AttemptContainerDetail(SchemaModel):
    ContainerInstanceArn: Optional[str] = custom_field(default=None)
    TaskArn: Optional[str] = custom_field(default=None)
    ExitCode: Optional[int] = custom_field(default=None)
    Reason: Optional[str] = custom_field(default=None)
    LogStreamName: Optional[str] = custom_field(default=None)


@dataclass
class AttemptDetail(SchemaModel):
    Container: Optional[AttemptContainerDetail] = custom_field(
        mm_field=AttemptContainerDetail.as_mm_field(), default=None
    )
    StartedAt: Optional[int] = custom_field(default=None)
    StoppedAt: Optional[int] = custom_field(default=None)
    StatusReason: Optional[str] = custom_field(default=None)

    @property
    def duration(self) -> Optional[int]:
        if self.StoppedAt and self.StartedAt:
            return self.StoppedAt - self.StartedAt
        return None

    @property
    def container_instance_arn(self) -> Optional[str]:
        if self.Container:
            return self.Container.ContainerInstanceArn
        return None

    @property
    def container_task_arn(self) -> Optional[str]:
        if self.Container:
            return self.Container.TaskArn
        return None


@dataclass
class BatchJobDetail(SchemaModel):
    JobName: str = custom_field()
    JobId: str = custom_field()
    JobQueue: str = custom_field()
    Status: str = custom_field()
    StartedAt: int = custom_field()
    JobDefinition: str = custom_field()

    # Optional
    JobArn: Optional[str] = custom_field(default=None, repr=False)
    StatusReason: Optional[str] = custom_field(default=None, repr=False)
    Attempts: List[AttemptDetail] = custom_field(
        mm_field=ListField(AttemptDetail.as_mm_field()), default_factory=list, repr=False
    )
    Container: Optional[ContainerDetail] = custom_field(
        mm_field=ContainerDetail.as_mm_field(), default=None, repr=False
    )
    Parameters: Dict[str, str] = custom_field(default_factory=dict, repr=False)
    CreatedAt: Optional[int] = custom_field(default=None, repr=False)
    StoppedAt: Optional[int] = custom_field(default=None, repr=False)
    IsCancelled: Optional[bool] = custom_field(default=None, repr=False)
    IsTerminated: Optional[bool] = custom_field(default=None, repr=False)

    @property
    def duration(self) -> Optional[int]:
        if self.StoppedAt and self.StartedAt:
            return self.StoppedAt - self.StartedAt
        return None

    @property
    def container_name_and_tag(self) -> Tuple[str, Optional[str]]:
        if self.Container:
            (container, container_tag) = self.Container.Image.split(":", maxsplit=1)
            return (container, container_tag)
        return ("NotAvailable", None)

    @property
    def container_tag(self) -> Optional[str]:
        return self.container_name_and_tag[1]

    @property
    def container_environment(self) -> Dict[str, str]:
        return {
            env_var.Name: env_var.Value
            for env_var in (self.Container.Environment if self.Container else {})
        }

    @property
    def container_instance_arn(self) -> Optional[str]:
        if self.Container:
            return self.Container.ContainerInstanceArn
        return None

    @property
    def container_instance_arns(self) -> List[str]:
        return [
            _
            for _ in set(
                [
                    self.container_instance_arn,
                    *[
                        a.Container.ContainerInstanceArn
                        for a in self.Attempts or []
                        if a.Container
                    ],
                ]
            )
            if _ is not None
        ]

    @property
    def container_task_arn(self) -> Optional[str]:
        if self.Container:
            return self.Container.TaskArn
        return None
