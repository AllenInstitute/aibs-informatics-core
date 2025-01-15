import unittest

from pytest import mark, param

from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution.metadata import DemandExecutionMetadata
from aibs_informatics_core.models.demand_execution.model import DemandExecution
from aibs_informatics_core.models.demand_execution.parameters import DemandExecutionParameters
from aibs_informatics_core.models.unique_ids import UniqueID

THIS_UUID = UniqueID.create()
ANOTHER_UUID = UniqueID.create()

S3_URI = S3URI.build(bucket_name="bucket", key="key")


EXECUTION_IMAGE = "051791135335.dkr.ecr.us-west-2.amazonaws.com/test_image:latest"
ANOTHER_EXECUTION_IMAGE = "051791135335.dkr.ecr.us-west-2.amazonaws.com/another_image:latest"


def get_any_demand_execution(
    execution_type: str = None,
    execution_id: str = None,
    execution_image: str = None,
    execution_parameters: DemandExecutionParameters = None,
    execution_metadata: DemandExecutionMetadata = None,
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
