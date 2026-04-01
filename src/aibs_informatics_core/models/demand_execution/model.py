from typing import Any, cast

from pydantic import Field

from aibs_informatics_core.models.base import PydanticBaseModel
from aibs_informatics_core.models.demand_execution.metadata import DemandExecutionMetadata
from aibs_informatics_core.models.demand_execution.parameters import DemandExecutionParameters
from aibs_informatics_core.models.demand_execution.platform import ExecutionPlatform
from aibs_informatics_core.models.demand_execution.resource_requirements import (
    DemandResourceRequirements,
)
from aibs_informatics_core.utils.hashing import sha256_hexdigest
from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.time import get_current_time


class DemandExecution(PydanticBaseModel):
    execution_type: str
    execution_id: str
    execution_image: str
    execution_parameters: DemandExecutionParameters = Field(
        default_factory=DemandExecutionParameters
    )
    execution_metadata: DemandExecutionMetadata = Field(default_factory=DemandExecutionMetadata)
    execution_platform: ExecutionPlatform = Field(default_factory=ExecutionPlatform)
    resource_requirements: DemandResourceRequirements = Field(
        default_factory=DemandResourceRequirements
    )

    def get_execution_hash(self, strict: bool = True) -> str:
        hash_components: list[Any] = [
            self.execution_type,
            self.execution_image,
            self.execution_parameters.command,
        ]
        if strict:
            hash_components.extend(
                [
                    self.execution_id,
                    # This ensures that the params are sanitized properly before hashing
                    self.execution_parameters.sanitize_serialized_params(
                        self.execution_parameters.params
                    ),
                    self.execution_parameters.inputs,
                    self.execution_parameters.outputs,
                ]
            )
        return sha256_hexdigest(cast(JSON, hash_components))

    def generate_execution_name(self) -> str:
        """Creates a execution name for state machine execution

        Pattern (SUBJECT TO CHANGE): "{DEMAND_ID}-xxxxxx"

        The execution name is prefixed by demand Id to be more easily discoverable

        """
        return f"{self.execution_id}-{get_current_time().strftime('%Y%m%dT%H%M%S')}"
