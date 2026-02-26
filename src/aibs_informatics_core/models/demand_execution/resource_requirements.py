from typing import ClassVar

from pydantic import model_serializer

from aibs_informatics_core.models.base import PydanticBaseModel


class DemandResourceRequirements(PydanticBaseModel):
    invalid_constraints: ClassVar[set] = {0, None}  # remove None and 0 entries

    gpu: int | None = None
    memory: int | None = None
    vcpus: int | None = None

    @model_serializer(mode="wrap")
    def _filter_invalid_constraints(self, handler):
        cls = type(self)
        data = handler(self)
        return {k: v for k, v in data.items() if v not in cls.invalid_constraints}
