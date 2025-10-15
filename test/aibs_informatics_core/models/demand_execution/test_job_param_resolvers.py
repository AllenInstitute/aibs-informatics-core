from typing import List, Optional

from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution.job_param import JobParam
from aibs_informatics_core.models.demand_execution.job_param_resolver import JobParamResolver
from aibs_informatics_core.models.unique_ids import UniqueID
from test.base import does_not_raise

THIS_UUID = UniqueID.create()
ANOTHER_UUID = UniqueID.create()

S3_URI = S3URI.build(bucket_name="bucket", key="key")


@mark.parametrize(
    "job_params, expected, raises_error",
    [
        param(
            [
                JobParam("param_foo", "foo"),
                JobParam("param_bar", "bar"),
                JobParam("param_qaz", "qaz"),
            ],
            [
                JobParam("param_foo", "foo"),
                JobParam("param_bar", "bar"),
                JobParam("param_qaz", "qaz"),
            ],
            does_not_raise(),
            id="Simple case, no references",
        ),
        param(
            [
                JobParam("param_a", "foo_${param_b}"),
                JobParam("param_b", "bar"),
            ],
            [
                JobParam("param_a", "foo_bar"),
                JobParam("param_b", "bar"),
            ],
            does_not_raise(),
            id="Simple case with reference",
        ),
        param(
            [
                JobParam("param_a", "foo_${param_B}"),
                JobParam("param-b", "bar"),
            ],
            [
                JobParam("param_a", "foo_bar"),
                JobParam("param-b", "bar"),
            ],
            does_not_raise(),
            id="Simple case with reference to unnormalized param name",
        ),
        param(
            [
                JobParam("param_a", "a"),
                JobParam("param_b", "b"),
                JobParam("param_c", "c"),
                JobParam("param_d", "d"),
                JobParam("param_ab", "${param_a}${param_b}"),
                JobParam("param_cd", "${param_c}${param_d}"),
                JobParam("param_abcd", "${param_ab}${param_cd}"),
                JobParam("param_aababcd", "${param_a}${param_ab}${param_ab}${param_cd}"),
            ],
            [
                JobParam("param_a", "a"),
                JobParam("param_b", "b"),
                JobParam("param_c", "c"),
                JobParam("param_d", "d"),
                JobParam("param_ab", "ab"),
                JobParam("param_cd", "cd"),
                JobParam("param_abcd", "abcd"),
                JobParam("param_aababcd", "aababcd"),
            ],
            does_not_raise(),
            id="Complex case of nested references",
        ),
        param(
            [
                JobParam("param_a", "${param_a}"),
            ],
            None,
            raises(ValidationError),
            id="Invalid self reference",
        ),
        param(
            [
                JobParam("param_a", "bar"),
                JobParam("param_A", "foo"),
            ],
            None,
            raises(ValidationError),
            id="Invalid colliding references",
        ),
        param(
            [
                JobParam("param_a", "${param_b}"),
                JobParam("param_b", "${param_c}"),
                JobParam("param_c", "${param_a}"),
            ],
            None,
            raises(ValidationError),
            id="Invalid cyclical references",
        ),
    ],
)
def test__JobParamResolver__resolve_references__behaves_as_intended(
    job_params: List[JobParam],
    expected: Optional[List[JobParam]],
    raises_error,
):
    with raises_error:
        actual = JobParamResolver.resolve_references(job_params)
    if expected is not None:
        assert actual == expected
