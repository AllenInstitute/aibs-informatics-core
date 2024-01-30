from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Optional, Set

import marshmallow as mm

from aibs_informatics_core.models.base.model import SchemaModel


@dataclass
class DemandResourceRequirements(SchemaModel):
    invalid_constraints: ClassVar[Set] = {0, None}  # remove None and 0 entries

    gpu: Optional[int] = None
    memory: Optional[int] = None
    vcpus: Optional[int] = None

    @classmethod
    @mm.post_dump
    def _filter_invalid_constraints(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        return {k: v for k, v in data.items() if v not in cls.invalid_constraints}
