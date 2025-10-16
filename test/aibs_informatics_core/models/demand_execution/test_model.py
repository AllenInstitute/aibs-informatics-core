import unittest
from typing import Optional

from pytest import mark, param

from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution.metadata import DemandExecutionMetadata
from aibs_informatics_core.models.demand_execution.model import DemandExecution
from aibs_informatics_core.models.demand_execution.parameters import DemandExecutionParameters
from aibs_informatics_core.models.demand_execution.platform import (
    AWSBatchExecutionPlatform,
    ExecutionPlatform,
)
from aibs_informatics_core.models.unique_ids import UniqueID

THIS_UUID = UniqueID.create()
ANOTHER_UUID = UniqueID.create()

S3_URI = S3URI.build(bucket_name="bucket", key="key")


EXECUTION_IMAGE = "051791135335.dkr.ecr.us-west-2.amazonaws.com/test_image:latest"
ANOTHER_EXECUTION_IMAGE = "051791135335.dkr.ecr.us-west-2.amazonaws.com/another_image:latest"


def get_any_demand_execution(
    execution_type: Optional[str] = None,
    execution_id: Optional[str] = None,
    execution_image: Optional[str] = None,
    execution_parameters: Optional[DemandExecutionParameters] = None,
    execution_metadata: Optional[DemandExecutionMetadata] = None,
) -> DemandExecution:
    return DemandExecution(
        execution_id=execution_id or THIS_UUID,
        execution_type=execution_type or "custom",
        execution_image=execution_image or EXECUTION_IMAGE,
        execution_parameters=execution_parameters
        or DemandExecutionParameters(
            output_s3_prefix=S3_URI,
            verbosity=True,
        ),
        execution_metadata=execution_metadata or DemandExecutionMetadata(),
    )


@mark.parametrize(
    "this_execution, that_execution, not_strict_equality, strict_equality",
    [
        param(
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            True,
            True,
            id="Executions with no diffs generate same not-/strict hash: True/True",
        ),
        param(
            get_any_demand_execution(
                execution_id=THIS_UUID,
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            get_any_demand_execution(
                execution_id=ANOTHER_UUID,
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            True,
            False,
            id="Executions with diff execution ids generate same not-/strict hash: True/False",
        ),
        param(
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "b"}
                ),
            ),
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            True,
            False,
            id="Executions with different params generate same not-/strict hash: True/False",
        ),
        param(
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe2"], params={"a": "a"}
                ),
            ),
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            False,
            False,
            id="Executions with different commands generate same not-/strict hash: False/False",
        ),
        param(
            get_any_demand_execution(
                execution_type="operationA",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            get_any_demand_execution(
                execution_type="operationB",
                execution_image=EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    command=["my_exe"], params={"a": "a"}
                ),
            ),
            False,
            False,
            id="Executions with different exec types generate same not-/strict hash: False/False",
        ),
    ],
)
def test__DemandExecution__get_execution_hash__behaves_as_intended(
    this_execution: DemandExecution,
    that_execution: DemandExecution,
    not_strict_equality: bool,
    strict_equality: bool,
):
    this_not_strict_hash = this_execution.get_execution_hash(False)
    that_not_strict_hash = that_execution.get_execution_hash(False)
    this_strict_hash = this_execution.get_execution_hash(True)
    that_strict_hash = that_execution.get_execution_hash(True)

    if not_strict_equality:
        assert this_not_strict_hash == that_not_strict_hash
    else:
        assert this_not_strict_hash != that_not_strict_hash

    if strict_equality:
        assert this_strict_hash == that_strict_hash
    else:
        assert this_strict_hash != that_strict_hash


class DemandExecutionTests(unittest.TestCase):
    def test__generate_execution_name__generates_correct_pattern(self):
        demand_execution = get_any_demand_execution()
        execution_name = demand_execution.generate_execution_name()
        self.assertRegex(
            execution_name, rf"{demand_execution.execution_id}-[\d]{{{8}}}T[\d]{{{6}}}"
        )


def test__DemandExecution__to_dict_and_from_dict__works():
    demand_execution = get_any_demand_execution()
    as_dict = demand_execution.to_dict()
    from_dict = DemandExecution.from_dict(as_dict)
    assert from_dict == demand_execution


@mark.parametrize(
    "demand_execution, expected_dict",
    [
        param(
            get_any_demand_execution(),
            {
                "execution_id": str(THIS_UUID),
                "execution_type": "custom",
                "execution_image": EXECUTION_IMAGE,
                "execution_parameters": {
                    "command": [],
                    "params": {},
                    "inputs": [],
                    "outputs": [],
                    "outputs_metadata": {},
                    "output_s3_prefix": "s3://bucket/key",
                    "verbosity": True,
                },
                "execution_platform": {},
                "execution_metadata": {},
                "resource_requirements": {},
            },
            id="Default demand execution to_dict",
        ),
        param(
            DemandExecution(
                execution_id=str(THIS_UUID),
                execution_type="operationA",
                execution_image=ANOTHER_EXECUTION_IMAGE,
                execution_parameters=DemandExecutionParameters(
                    output_s3_prefix=S3_URI,
                    verbosity=True,
                    command=["my_exe"],
                    params={"a": "a"},
                    outputs=["a"],
                ),
                execution_metadata=DemandExecutionMetadata(tags={"tag1": "value1"}),
                execution_platform=ExecutionPlatform(
                    aws_batch=AWSBatchExecutionPlatform(
                        job_queue_name="my_job_queue",
                        job_role="arn:aws:iam::123456789012:role/MyRole",
                    )
                ),
            ),
            {
                "execution_id": str(THIS_UUID),
                "execution_type": "operationA",
                "execution_image": ANOTHER_EXECUTION_IMAGE,
                "execution_parameters": {
                    "command": ["my_exe"],
                    "params": {"a": "a"},
                    "inputs": [],
                    "outputs": ["a"],
                    "outputs_metadata": {},
                    "output_s3_prefix": "s3://bucket/key",
                    "verbosity": True,
                },
                "execution_metadata": {"tags": {"tag1": "value1"}},
                "execution_platform": {
                    "aws_batch": {
                        "job_queue_name": "my_job_queue",
                        "job_role": "arn:aws:iam::123456789012:role/MyRole",
                    }
                },
                "resource_requirements": {},
            },
            id="Custom demand execution to_dict",
        ),
    ],
)
def test__DemandExecution__to_dict(demand_execution, expected_dict):
    as_dict = demand_execution.to_dict()
    assert as_dict == expected_dict
