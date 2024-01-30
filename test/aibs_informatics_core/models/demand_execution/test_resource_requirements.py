from pytest import mark, param

from aibs_informatics_core.models.demand_execution.resource_requirements import (
    DemandResourceRequirements,
)


@mark.parametrize(
    "input_resources, output_resources",
    [
        param(
            {
                "gpu": 1,
                "memory": 64,
                "vcpus": 8,
            },
            {
                "gpu": 1,
                "memory": 64,
                "vcpus": 8,
            },
            id="Full",
        ),
        param(
            {
                "memory": 64,
                "vcpus": 8,
            },
            {
                "memory": 64,
                "vcpus": 8,
            },
            id="Partial",
        ),
        param(
            {
                "gpu": 0,
                "memory": 64,
                "vcpus": 8,
            },
            {
                "memory": 64,
                "vcpus": 8,
            },
            id="Zero",
        ),
        param(
            {
                "gpu": None,
                "memory": 64,
                "vcpus": 8,
            },
            {
                "memory": 64,
                "vcpus": 8,
            },
            id="None",
        ),
    ],
)
def test_resource_requirements(input_resources, output_resources):
    obtained = DemandResourceRequirements(**input_resources).to_dict()
    assert obtained == output_resources
