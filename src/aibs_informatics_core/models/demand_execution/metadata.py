from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from aibs_informatics_core.models.aws.sfn import ExecutionArn
from aibs_informatics_core.models.base import SchemaModel, custom_field, pre_load
from aibs_informatics_core.models.base.custom_fields import (
    BooleanField,
    CustomStringField,
    DictField,
    EnumField,
    ListField,
    StringField,
)
from aibs_informatics_core.models.status import Status


@dataclass
class DemandExecutionMetadata(SchemaModel):
    user: Optional[str] = custom_field(default=None)
    arn: Optional[ExecutionArn] = custom_field(
        mm_field=CustomStringField(ExecutionArn), default=None
    )
    tags: Optional[Dict[str, str]] = custom_field(
        mm_field=DictField(StringField(), StringField(), allow_none=True),
        default=None,
    )
    notify_on: Optional[Dict[Status, bool]] = custom_field(
        mm_field=DictField(keys=EnumField(Status), values=BooleanField(), allow_none=True),
        default=None,
    )
    notify_list: Optional[List[str]] = custom_field(
        mm_field=ListField(StringField(), allow_none=True),
        default=None,
    )

    @property
    def tag(self) -> Optional[str]:
        """Return all tags as a comma separated string if available.

        Example:
            >>> metadata = DemandExecutionMetadata(tags={"key": "value"})
            >>> metadata.tag
            'key=value'
            >>> metadata = DemandExecutionMetadata(tags={"key": "key"})
            >>> metadata.tag
            'key'
            >>> metadata = DemandExecutionMetadata(tags={"flag": "flag", "key": "value"})
            >>> metadata.tag
            'flag,key=value'
            >>> metadata = DemandExecutionMetadata(tags={})
            >>> metadata.tag
            None

        Returns:
            Optional[str]: Comma separated string of tags or None if no tags are available.

        """
        if self.tags:
            return ",".join([f"{k}={v}" if k != v else k for k, v in self.tags.items()])
        return None

    @classmethod
    @pre_load
    def sanitize_tags(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        norm_tags: dict[str, str] = {}
        if "tag" in data:
            tag = data.pop("tag")
            if isinstance(tag, (str, int)):
                norm_tags = {str(tag): str(tag)} | norm_tags
            elif isinstance(tag, list):
                norm_tags = {str(t): str(t) for t in tag} | norm_tags

        if "tags" in data:
            tags = data["tags"]
            if isinstance(tags, (str, int)):
                tags = dict(
                    [
                        (tag_part, tag_part)
                        if "=" not in tag_part
                        else cast(tuple[str, str], tuple(tag_part.split("=", 1)))
                        for tag_part in str(tags).split(",")
                    ]
                )
                data["tags"] = norm_tags | tags
            elif isinstance(tags, list):
                data["tags"] = norm_tags | {str(tag): str(tag) for tag in tags}
            elif isinstance(tags, dict):
                data["tags"] = norm_tags | tags
            else:
                raise ValueError(f"Invalid tags format: {tags}")
        elif norm_tags:
            data["tags"] = norm_tags
        return data
