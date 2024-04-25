__all__ = [
    "GWODemandRegistryEntry",
]

import datetime as dt
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Union

import marshmallow as mm

from aibs_informatics_core.models.aws.iam import UserId
from aibs_informatics_core.models.aws.sfn import ExecutionArn
from aibs_informatics_core.models.aws.sns import SNSTopicArn
from aibs_informatics_core.models.base import CustomAwareDateTime, IntegerField, MappingField, StringField
from aibs_informatics_core.models.base.custom_fields import (
    BooleanField,
    CustomStringField,
    FrozenSetField,
    DictField,
    EnumField,
    FrozenSetField,
    ListField,
    UnionField,
)
from aibs_informatics_core.models.base.field_utils import custom_field
from aibs_informatics_core.models.base.model import SchemaModel, pre_load, post_dump
from aibs_informatics_core.models.db.base import DBModel
from aibs_informatics_core.models.demand_execution.model import DemandExecution
from aibs_informatics_core.models.email_address import EmailAddress
from aibs_informatics_core.models.status import Status
from aibs_informatics_core.models.unique_ids import UniqueID
from aibs_informatics_core.utils.time import get_current_time

DEFAULT_USER = "anonymous"


@dataclass
class GWODemandRegistryEntry(DBModel):
    execution_id: UniqueID = custom_field(mm_field=UniqueID.as_mm_field())
    execution_type: str = custom_field(mm_field=StringField())
    request: dict = custom_field(mm_field=MappingField())
    status: Status = custom_field(mm_field=EnumField(Status))
    start_time: dt.datetime = custom_field(mm_field=CustomAwareDateTime(format="iso8601"))
    last_update_time: dt.datetime = custom_field(mm_field=CustomAwareDateTime(format="iso8601"))
    duration: int = custom_field(mm_field=IntegerField())
    message: Optional[str] = custom_field(mm_field=StringField(allow_none=True), default=None)
    user: Optional[str] = custom_field(mm_field=StringField(allow_none=True), default=None)
    aws_user_id: Optional[str] = custom_field(mm_field=StringField(allow_none=True), default=None)
    tag: Optional[str] = custom_field(mm_field=StringField(allow_none=True), default=None)
    notify_on: Optional[Dict[Status, bool]] = custom_field(
        mm_field=DictField(keys=EnumField(Status), values=BooleanField(), allow_none=True),
        default=None,
    )
    notify_list: Optional[List[str]] = custom_field(
        mm_field=ListField(StringField(), allow_none=True),
        default=None,
    )

    @property
    def execution_arn(self) -> Optional[ExecutionArn]:
        demand_execution = self.demand_execution
        return demand_execution.execution_metadata.arn if demand_execution else None

    @property
    def demand_execution(self) -> Optional[DemandExecution]:
        if DemandExecution.is_valid(self.request):
            return DemandExecution.from_dict(self.request)
        return None

    @property
    def elapsed_time(self) -> int:
        if self.status in ["AWAITING_TRIGGER", "IN_PROGRESS"]:
            return (get_current_time() - self.start_time).seconds
        else:
            return self.duration

    @classmethod
    @mm.pre_load
    @mm.post_dump
    def sanitize_message(cls, data: dict, **kwargs) -> dict:
        """Sanitizes the message for serialization/deserialization, if present

        Ensures that if message is not a string or none, that it is converted to str.
        """
        message = data.get("message")
        if message is not None and not isinstance(message, str):
            data["message"] = str(message)
        return data

    @classmethod
    @mm.pre_load
    @mm.post_dump
    def fill_user_fields(cls, data: dict, **kwargs) -> dict:
        """Cleans up user fields

        Ensures that if message is not a string or none, that it is converted to str.
        """
        aws_user_id = data.get("aws_user_id")
        user = data.get("user")
        if aws_user_id and (not user or user == DEFAULT_USER):
            try:
                aws_user_id = UserId(aws_user_id)
                user = aws_user_id.caller_specified_name
            except:
                pass
        if user:
            data["user"] = user
        return data



@dataclass
class DemandOutputResultEntry(DBModel):
    execution_id: UniqueID = custom_field(mm_field=UniqueID.as_mm_field())
    last_update_time: dt.datetime = custom_field(mm_field=CustomAwareDateTime(format="iso8601"))
    output: str = custom_field(mm_field=StringField())
    inputs: Set[str] = custom_field(mm_field=FrozenSetField(StringField()))
    


@dataclass
class DemandExecutionResults(DBModel):
    execution_id: UniqueID = custom_field(mm_field=UniqueID.as_mm_field())
    last_update_time: dt.datetime = custom_field(mm_field=CustomAwareDateTime(format="iso8601"))
    outputs: Dict[str, Set[str]] = custom_field(
        mm_field=MappingField(keys=StringField(), values=FrozenSetField(StringField()))
    )
    
    @classmethod
    @mm.pre_load
    def load_from_list(cls, data: Union[dict, list[dict]], **kwargs) -> dict:
        """Converts the output pair to a list of results"""
        if isinstance(data, list):
            outputs = [DemandOutputResultEntry.from_dict(_) for _ in data]
            last_update_time = max([_.last_update_time for _ in outputs])
            execution_id = outputs[0].execution_id
            data = {
                "execution_id": execution_id,
                "last_update_time": last_update_time,
                "outputs": {
                    _.output: _.inputs for _ in outputs
                }
            }
        return data

    def to_list(self) -> List[DemandOutputResultEntry]:
        """Converts the output pair to a list of results"""
        return [
            DemandOutputResultEntry(
                execution_id=self.execution_id,
                last_update_time=self.last_update_time,
                output=output,
                inputs=inputs,
            )
            for output, inputs in self.outputs.items()
        ]