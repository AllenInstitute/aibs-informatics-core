from dataclasses import dataclass
from typing import Any, ClassVar

import marshmallow as mm

from aibs_informatics_core.models.base.model import SchemaModel


@dataclass
class DemandResourceRequirements(SchemaModel):
    invalid_constraints: ClassVar[set] = {0, None}  # remove None and 0 entries

    gpu: int | None = None
    memory: int | None = None
    vcpus: int | None = None

    @classmethod
    @mm.post_dump
    def _filter_invalid_constraints(cls, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {k: v for k, v in data.items() if v not in cls.invalid_constraints}
