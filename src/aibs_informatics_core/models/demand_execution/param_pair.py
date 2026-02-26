from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from pydantic import field_validator

from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.base import (
    FrozenSetField,
    PydanticBaseModel,
    StringField,
    custom_field,
)
from aibs_informatics_core.models.base.custom_fields import UnionField
from aibs_informatics_core.models.demand_execution.job_param import ResolvableJobParam


class ParamPair(PydanticBaseModel):
    """PydanticBaseModel for an input and output parameter pairs as described in demand execution

    The values for input and output should correspond to the parameter key in the demand execution

    Scenarios:
        1. input is not None and output is not None (input and output)
            This is used to represent a single job that has both inputs and outputs (Most common)
        2. input and output are both None (no inputs or outputs)
            This is used to represent a single job that has no inputs or outputs
        3. input is None and output is not None (output only)
            This is used to represent a single job that has only outputs
        4. input is not None and output is None (input only)
            This is used to represent a single job that has only inputs

    """

    input: str | None = custom_field(mm_field=StringField(), default=None)
    output: str | None = custom_field(mm_field=StringField(), default=None)

    @classmethod
    def from_set_pairs(cls, *values: ParamSetPair) -> list[ParamPair]:
        return [pair for value in values for pair in value.to_pairs()]

    @classmethod
    def from_sets(cls, inputs: Iterable[str], outputs: Iterable[str]) -> list[ParamPair]:
        if not inputs and not outputs:
            return []
        elif not inputs:
            return [ParamPair(output=output) for output in outputs]
        elif not outputs:
            return [ParamPair(input=input) for input in inputs]
        return [ParamPair(input=input, output=output) for input in inputs for output in outputs]


class ParamSetPair(PydanticBaseModel):
    """PydanticBaseModel for a set of input and output parameter pairs as described in demand execution

    The values for inputs and outputs should correspond to the parameter keys in the
    demand execution.

    Scenarios:
        1. inputs and outputs are not empty
            This accounts for set of related inputs and outputs
        2. inputs and outputs are both empty
            This is used to represent a single job that has no inputs or outputs
        3. inputs is empty and outputs is not empty
            This is used to represent a single job that has only outputs
        4. inputs is not empty and outputs is empty
            This is used to represent a single job that has only inputs
    """

    inputs: frozenset[str] = custom_field(
        mm_field=FrozenSetField(StringField), default_factory=frozenset
    )
    outputs: frozenset[str] = custom_field(
        mm_field=FrozenSetField(StringField), default_factory=frozenset
    )

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def _coerce_setlike(cls, value):
        if value is None:
            return frozenset()
        if isinstance(value, dict):
            return frozenset(value.keys())
        if isinstance(value, (set, frozenset, list, tuple)):
            return frozenset(value)
        return value

    def model_post_init(self, __context) -> None:
        if not isinstance(self.inputs, frozenset):
            self.inputs = frozenset(self.inputs)
        if not isinstance(self.outputs, frozenset):
            self.outputs = frozenset(self.outputs)

    def add_inputs(self, *inputs: str):
        self.inputs = self.inputs.union(inputs)

    def add_outputs(self, *outputs: str):
        self.outputs = self.outputs.union(outputs)

    def remove_inputs(self, *inputs: str):
        self.inputs = self.inputs.difference(inputs)

    def remove_outputs(self, *outputs: str):
        self.outputs = self.outputs.difference(outputs)

    def to_pairs(self) -> list[ParamPair]:
        return ParamPair.from_sets(inputs=self.inputs, outputs=self.outputs)

    @classmethod
    def from_pairs(cls, *pairs: ParamPair) -> list[ParamSetPair]:
        """Converts a list of ParamPairs to a list of ParamSetPairs

        This is useful for grouping ParamPairs by output

        Returns:
            A list of ParamSetPairs
        """
        # group pairs only by outputs
        output_set_pairs: dict[str | None, ParamSetPair] = {}
        for pair in pairs:
            if pair.output not in output_set_pairs:
                output_set_pairs[pair.output] = ParamSetPair(
                    outputs=frozenset({pair.output}) if pair.output else frozenset()
                )
            if pair.input is not None:
                output_set_pairs[pair.output].add_inputs(pair.input)
        return list(output_set_pairs.values())


@dataclass(frozen=True)
class JobParamPair:
    """models an input and output resolved parameter pair as described in demand execution

    The values for input and outputs should account for both the parameter name and the
    remote location of the parameter value. The remote location can be a S3URI or other
    remote location.

    This captures all information about a parameter

    Scenarios:
        1. input is not None and output is not None (input and output)
            This is used to represent a single job that has both inputs and outputs (Most common)
        2. input and output are both None (no inputs or outputs)
            This is used to represent a single job that has no inputs or outputs
        3. input is None and output is not None (output only)
            This is used to represent a single job that has only outputs
        4. input is not None and output is None (input only)
            This is used to represent a single job that has only inputs
    """  # noqa: E501

    input: ResolvableJobParam | None = None
    output: ResolvableJobParam | None = None

    @classmethod
    def from_sets(
        cls, inputs: Iterable[ResolvableJobParam], outputs: Iterable[ResolvableJobParam]
    ) -> list[JobParamPair]:
        if not inputs and not outputs:
            return []
        elif not inputs:
            return [JobParamPair(output=output) for output in outputs]
        elif not outputs:
            return [JobParamPair(input=input) for input in inputs]
        return [JobParamPair(input=input, output=output) for input in inputs for output in outputs]

    @classmethod
    def from_set_pairs(cls, *values: JobParamSetPair) -> list[JobParamPair]:
        return [pair for value in values for pair in value.to_pairs()]


@dataclass
class JobParamSetPair:
    """models a set of input and output resolved parameter pairs as described in demand execution

    The values for inputs and outputs should account for both the parameter name and the remote location.
    The remote location can be a S3URI or other remote location.

    This captures all information about a parameter

    Scenarios:
        1. inputs and outputs are not empty
            This accounts for set of related inputs and outputs
        2. inputs and outputs are both empty
            This is used to represent a single job that has no inputs or outputs
        3. inputs is empty and outputs is not empty
            This is used to represent a single job that has only outputs
        4. inputs is not empty and outputs is empty
            This is used to represent a single job that has only inputs
    """  # noqa: E501

    inputs: frozenset[ResolvableJobParam] = field(default_factory=frozenset)
    outputs: frozenset[ResolvableJobParam] = field(default_factory=frozenset)

    def __post_init__(self):
        if not isinstance(self.inputs, frozenset):
            self.inputs = frozenset(self.inputs)
        if not isinstance(self.outputs, frozenset):
            self.outputs = frozenset(self.outputs)

    def add_inputs(self, *inputs: ResolvableJobParam):
        self.inputs = self.inputs.union(inputs)

    def add_outputs(self, *outputs: ResolvableJobParam):
        self.outputs = self.outputs.union(outputs)

    def remove_inputs(self, *inputs: ResolvableJobParam):
        self.inputs = self.inputs.difference(inputs)

    def remove_outputs(self, *outputs: ResolvableJobParam):
        self.outputs = self.outputs.difference(outputs)

    def to_pairs(self) -> list[JobParamPair]:
        return JobParamPair.from_sets(inputs=self.inputs, outputs=self.outputs)

    @classmethod
    def from_pairs(cls, *pairs: JobParamPair) -> list[JobParamSetPair]:
        """Converts a list of JobParamPairs to a list of JobParamSetPairs

        This is useful for grouping JobParamPairs by output

        Returns:
            A list of JobParamSetPairs
        """
        # group pairs only by outputs
        output_set_pairs: dict[ResolvableJobParam | None, JobParamSetPair] = {}
        for pair in pairs:
            if pair.output not in output_set_pairs:
                output_set_pairs[pair.output] = JobParamSetPair(
                    outputs=frozenset({pair.output}) if pair.output else frozenset()
                )
            if pair.input is not None:
                output_set_pairs[pair.output].add_inputs(pair.input)
        return list(output_set_pairs.values())


# ResolvableID = Union[S3URI, ...]
# TODO: need to add additional types.
ResolvableID = S3URI


class ResolvedParamSetPair(PydanticBaseModel):
    """PydanticBaseModel for a set of input and output resolved parameter pairs as described in demand execution

    This is the other side of the ParamSetPair coin. This is used to represent a set of
    inputs and outputs' remote locations. The remote location can be a S3URI or other
    remote location.

    This only captures the remote location of a parameter. It does not capture the parameter name.

    """  # noqa: E501

    inputs: frozenset[ResolvableID] = custom_field(
        mm_field=FrozenSetField(
            UnionField(
                [
                    (S3URI, S3URI.as_mm_field()),
                ]
            )
        ),
        default_factory=frozenset,
    )
    outputs: frozenset[ResolvableID] = custom_field(
        mm_field=FrozenSetField(
            UnionField(
                [
                    (S3URI, S3URI.as_mm_field()),
                ]
            )
        ),
        default_factory=frozenset,
    )

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def _coerce_setlike(cls, value):
        if value is None:
            return frozenset()
        if isinstance(value, dict):
            return frozenset(value.keys())
        if isinstance(value, (set, frozenset, list, tuple)):
            return frozenset(value)
        return value

    def model_post_init(self, __context) -> None:
        if not isinstance(self.inputs, frozenset):
            self.inputs = frozenset(self.inputs)
        if not isinstance(self.outputs, frozenset):
            self.outputs = frozenset(self.outputs)

    def add_inputs(self, *inputs: ResolvableID):
        self.inputs = self.inputs.union(inputs)

    def add_outputs(self, *outputs: ResolvableID):
        self.outputs = self.outputs.union(outputs)

    def remove_inputs(self, *inputs: ResolvableID):
        self.inputs = self.inputs.difference(inputs)

    def remove_outputs(self, *outputs: ResolvableID):
        self.outputs = self.outputs.difference(outputs)
