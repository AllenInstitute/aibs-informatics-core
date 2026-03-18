from typing import Any, ClassVar

from pydantic import model_validator

from aibs_informatics_core.models.base.model import PydanticBaseModel


class DemandResourceRequirements(PydanticBaseModel):
    invalid_constraints: ClassVar[set] = {0, None}  # remove None and 0 entries

    gpu: int | None = None
    memory: int | None = None
    vcpus: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _filter_invalid_constraints(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in data.items() if v not in cls.invalid_constraints}
