import logging
from typing import Any, cast

from pydantic import model_validator

from aibs_informatics_core.models.aws.sfn import ExecutionArn
from aibs_informatics_core.models.base import PydanticBaseModel
from aibs_informatics_core.models.status import Status


class DemandExecutionMetadata(PydanticBaseModel):
    user: str | None = None
    arn: ExecutionArn | None = None
    tags: dict[str, str] | None = None
    notify_on: dict[Status, bool] | None = None
    notify_list: list[str] | None = None

    @property
    def tag(self) -> str | None:
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
            Comma separated string of tags or None if no tags are available.

        """
        if self.tags:
            return ",".join([f"{k}={v}" if k != v else k for k, v in self.tags.items()])
        return None

    @model_validator(mode="before")
    @classmethod
    def _sanitize_tags(cls, data: Any) -> dict[str, Any]:
        """Sanitize tags and tag fields in the input data.

        If the `tag` field is present, it will be converted to a dictionary format. It supports
        both string and list formats. `tag` can include multiple tags separated by commas.

        By contrast, the `tags` field is expected to be a dictionary. If both `tag` and `tags` are
        present, they will be merged, with `tags` taking precedence.

        The `tag` field is deprecated and will be removed in a future version. It is recommended to
        use the `tags` field exclusively for tagging.

        TODO: Once we have datafixes for the places where demand execution metadata is used, we
        can remove this method and the `tag` field from the model. The `tags` field should be used
        exclusively.

        """
        norm_tags: dict[str, str] = {}
        if "tag" in data:
            tag_value = data.pop("tag")
            if isinstance(tag_value, (str, int)):
                tag_value = [tag_value]

            if isinstance(tag_value, list) and all([isinstance(_, (str, int)) for _ in tag_value]):
                norm_tags = dict(
                    [
                        (tag_part, tag_part)
                        if "=" not in tag_part
                        else cast(tuple[str, str], tuple(tag_part.split("=", 1)))
                        for _ in tag_value
                        for tag_part in str(_).split(",")
                    ]
                )
            else:
                logging.warning(
                    f"Invalid tag format ({type(tag_value)}): {tag_value}. "
                    "Expected str, int, or list of str/int. Ignoring."
                )

        if "tags" in data:
            tags = data["tags"]
            if isinstance(tags, dict):
                data["tags"] = norm_tags | tags
            else:
                raise ValueError(f"Invalid tags format ({type(tags)}): {tags}")
        elif norm_tags:
            data["tags"] = norm_tags
        return data
