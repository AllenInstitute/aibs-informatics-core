from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from aibs_informatics_core.models.aws.sfn import ExecutionArn
from aibs_informatics_core.models.base import SchemaModel, custom_field
from aibs_informatics_core.models.base.custom_fields import (
    BooleanField,
    CustomStringField,
    DictField,
    EnumField,
    ListField,
    StringField,
    UnionField,
)
from aibs_informatics_core.models.status import Status


@dataclass
class DemandExecutionMetadata(SchemaModel):
    user: Optional[str] = custom_field(default=None)
    arn: Optional[ExecutionArn] = custom_field(
        mm_field=CustomStringField(ExecutionArn), default=None
    )
    tag: Optional[str] = custom_field(default=None)
    notify_on: Optional[Dict[Status, bool]] = custom_field(
        mm_field=DictField(keys=EnumField(Status), values=BooleanField(), allow_none=True),
        default=None,
    )
    notify_list: Optional[List[str]] = custom_field(
        mm_field=ListField(StringField(), allow_none=True),
        default=None,
    )
