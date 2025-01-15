from test.base import does_not_raise
from typing import List
from unittest import mock

from pytest import fixture, mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution import (
    DemandExecutionParameters,
    DownloadableJobParam,
    JobParam,
    UploadableJobParam,
)
from aibs_informatics_core.models.demand_execution.param_pair import (
    JobParamPair,
    JobParamSetPair,
    ParamPair,
    ParamSetPair,
)
from aibs_informatics_core.models.demand_execution.resolvables import Resolvable
from aibs_informatics_core.models.unique_ids import UniqueID

THIS_UUID = UniqueID.create()
THAT_UUID = UniqueID.create()

S3_URI = S3URI.build(bucket_name="bucket", key="key")
ANOTHER_S3_URI = S3URI.build(bucket_name="bucket", key="key2")

S3_PREFIX = S3URI.build(bucket_name="bucket", key="prefix/")

# def test__refresh_params__no_args():

#     class CustomExecutionParameters(DemandExecutionParameters):

#         @refresh_params
#         def add_wonky_inputs(self, inputs: List[str]) -> List[str]:
#             return inputs + ["wonky_input"]


@fixture(scope="function")
def demand_execution_parameters():
    return DemandExecutionParameters(
        command=[],
        inputs=["param_in"],
        outputs=["param_out"],
        params={
            "param_in": S3_URI,
            "CapitalizedParam": "foo",
            "UPPERCASE_PARAM": "bar",
            "lowercase_param": "qaz",
            "param": "foo",
            "param_out": "bar",
        },
        output_s3_prefix=S3_PREFIX,
    )


@mark.parametrize(
    "parameters, expected_resolved_command, expected_job_params",
    [
        param(
            DemandExecutionParameters(
                command=["cmd", "contains=${param_bool}", "${param_with_hyphen}"],
                inputs=["param_in"],
                params={
                    "param_with_ref": "${param_out_with_ref}",
                    "param_with_refs": "${param_out_no_ref}_bar_${param_no_ref}",
                    "param_no_ref": "qaz",
                    "param_bool": False,
                    "param_in": S3_URI,
                    "param_out_no_ref": "foo",
                    "param_with-hyphen": 1,
                    "param_out_with_ref": "${param_no_ref}_bar",
                },
                outputs=["param_out_no_ref", "param_out_with_ref"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            ["cmd", "contains=False", "1"],
            [
                JobParam("param_with_ref", "qaz_bar"),
                JobParam("param_with_refs", "foo_bar_qaz"),
                JobParam("param_no_ref", "qaz"),
                JobParam("param_bool", "False"),
                DownloadableJobParam("param_in", "tmp558ca153", S3_URI),
                UploadableJobParam("param_out_no_ref", "foo", "s3://bucket/key/foo"),
                JobParam(name="param_with-hyphen", value="1"),
                UploadableJobParam("param_out_with_ref", "qaz_bar", "s3://bucket/key/qaz_bar"),
            ],
        ),
        param(
            DemandExecutionParameters(
                command=[],
                inputs=["param_in"],
                params={
                    "param_with_ref": "${param_out_with_ref}",
                    "param_with_refs": "${param_out_no_ref}_bar_${param_no_ref}",
                    "param_no_ref": "qaz",
                    "param_in": Resolvable(local="my_path", remote=S3_URI).to_dict(),
                    "param_in_with_ref": "${param_in}/${param_out_no_ref}",
                    "param_out_no_ref": "foo",
                    "param_out_with_ref": "${param_no_ref}_bar",
                },
                outputs=["param_out_no_ref", "param_out_with_ref"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            [],
            [
                JobParam("param_with_ref", "qaz_bar"),
                JobParam("param_with_refs", "foo_bar_qaz"),
                JobParam("param_no_ref", "qaz"),
                DownloadableJobParam("param_in", "my_path", S3_URI),
                JobParam("param_in_with_ref", "my_path/foo"),
                UploadableJobParam("param_out_no_ref", "foo", "s3://bucket/key/foo"),
                UploadableJobParam("param_out_with_ref", "qaz_bar", "s3://bucket/key/qaz_bar"),
            ],
        ),
    ],
)
def test__DemandExecutionParameters__job_params_returns_expected_result(
    parameters: DemandExecutionParameters,
    expected_resolved_command: List[str],
    expected_job_params: List[JobParam],
):
    assert parameters.resolved_command == expected_resolved_command
    assert parameters.job_params == expected_job_params


@mark.parametrize(
    "parameters_dict, raises_error",
    [
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_in": S3_URI,
                    "param": "foo",
                    "param_out": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            does_not_raise(),
            id="Validation passes with simple case of references",
        ),
        param(
            dict(
                command=[],
                inputs=[],
                params={},
                outputs=[],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            does_not_raise(),
            id="Validation passes with simple case with empty params",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_with_ref": "${param_out_with_ref}",
                    "param_with_refs": "${param_out_no_ref}_bar_${param_no_ref}",
                    "param_no_ref": "qaz",
                    "param_in": S3_URI,
                    "param_out_no_ref": "foo",
                    "param_out_with_ref": "${param_no_ref}_bar",
                },
                outputs=["param_out_no_ref", "param_out_with_ref"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            does_not_raise(),
            id="Validation passes with complex case of references",
        ),
        param(
            dict(
                command=[],
                inputs=["PARAM_in"],
                params={
                    "param_with_ref": "${param_OUT_with_ref}",
                    "param_no_ref": "qaz",
                    "param-in": S3_URI,
                    "param_out-no_ref": "foo",
                    "param_out_with_ref": "${param_no_ref}_bar",
                },
                outputs=["param_out_no_ref", "PARAM_OUT-with_ReF"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            does_not_raise(),
            id="Validations pass even with unnormalized param names",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={"param_in": S3_URI},
                outputs=["PARAM_IN"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid overlap of input / output values",
        ),
        param(
            dict(
                command=[],
                inputs=[],
                params={"param_out": "${param_out}"},
                outputs=["PARAM_OUT"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid self reference in param value",
        ),
        param(
            dict(
                command=[],
                inputs=[],
                params={"param_out": "foo", "param-out": "bar"},
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid param values that collide",
        ),
        param(
            dict(
                command=[],
                inputs=[],
                params={"param_out": "foo"},
                outputs=["param_outs"],
                output_s3_prefix=S3_URI,
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid missing reference in params",
        ),
        param(
            dict(
                command=[],
                inputs=[],
                params={"param_out": "foo"},
                outputs=["param_outs"],
                verbosity=True,
            ),
            raises(ValueError),
            id="Invalid missing output s3 prefix for output param",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in1", "param_in2", "param_in3"],
                params={
                    "param_in1": S3_URI,
                    "param_in2": ANOTHER_S3_URI,
                    "param_in3": "gs://bucket/key",
                    "param": "foo",
                    "param_out1": "bar",
                    "param_out2": "qaz",
                    "param_out3": "${param_out2}/abc",
                },
                output_s3_prefix=S3_URI,
                outputs=["param_out1", "param_out2", "param_out3"],
                param_set_pair_overrides=[
                    {"inputs": ["param_in1"], "outputs": ["param_out1"]},
                    {"input": "param_in2", "output": "param_out2"},
                    {"input": "param_in3"},
                    {"output": "param_out3"},
                ],
                verbosity=True,
            ),
            does_not_raise(),
            id="Validation passes with complex param pair overrides",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_in": S3_URI,
                    "param": "foo",
                    "param_out": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                input_output_pars=[{"inputs": [], "outputs": []}],
                verbosity=True,
            ),
            does_not_raise(),
            id="Validation passes with empty case of input_output",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_in": S3_URI,
                    "param": "foo",
                    "param_out": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                input_output_pairs=[
                    {
                        "inputs": ["param_in", "not_a_param"],
                        "outputs": ["param_out"],
                    }
                ],
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid input reference in input_output",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_in": S3_URI,
                    "param": "foo",
                    "param_out": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                input_output_pairs=[
                    {
                        "inputs": ["param_in"],
                        "outputs": ["param_out", "not_a_param"],
                    }
                ],
                verbosity=True,
            ),
            raises(ValidationError),
            id="Invalid output reference in input_output",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in1", "param_in2"],
                params={
                    "param_in1": S3_URI,
                    "param_in2": S3_URI,
                    "param": "foo",
                    "param_out": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                input_output_pairs=[
                    {
                        "inputs": ["param_in1"],
                        "outputs": ["param_out"],
                    },
                    {
                        "inputs": ["param_in2"],
                        "outputs": ["param_out"],
                    },
                ],
                verbosity=True,
            ),
            raises(ValidationError),
            id="Duplicate output reference in input_output",
        ),
        param(
            dict(
                command=[],
                inputs=["param_in"],
                params={
                    "param_in": S3_URI,
                    "param": "foo",
                    "param_out1": "bar",
                    "param_out2": "bar",
                },
                outputs=["param_out"],
                output_s3_prefix=S3_URI,
                input_output_pairs=[
                    {
                        "inputs": ["param_in"],
                        "outputs": ["param_out1"],
                    },
                    {
                        "inputs": ["param_in"],
                        "outputs": ["param_out2"],
                    },
                ],
                verbosity=True,
            ),
            raises(ValidationError),
            id="Duplicate input reference in input_output",
        ),
    ],
)
def test__DemandExecutionParameters__from_dict__validation_works_as_intended(
    parameters_dict: dict,
    raises_error,
):
    with raises_error:
        DemandExecutionParameters.from_dict(parameters_dict)


@mark.parametrize(
    "parameters, expected_param_set_pairs, expected_param_pairs",
    [
        param(
            DemandExecutionParameters(
                command=[],
                inputs=["param_in1", "param_in2"],
                params={
                    "param_with_ref": "${param_out2}",
                    "param_with_refs": "${param_out1}_bar_${param_no_ref}",
                    "param_no_ref": "qaz",
                    "param_in1": Resolvable(local="my_path1", remote=S3_URI).to_dict(),
                    "param_in2": Resolvable(local="my_path2", remote=S3_URI).to_dict(),
                    "param_in_with_ref": "${param_in1}/${param_out1}",
                    "param_out1": "foo",
                    "param_out2": "${param_no_ref}_bar",
                },
                outputs=["param_out1", "param_out2"],
                output_s3_prefix=S3_URI,
            ),
            [
                ParamSetPair(
                    inputs=frozenset({"param_in1", "param_in2"}), outputs=frozenset({"param_out1"})
                ),
                ParamSetPair(
                    inputs=frozenset({"param_in1", "param_in2"}), outputs=frozenset({"param_out2"})
                ),
            ],
            [
                ParamPair(input="param_in1", output="param_out1"),
                ParamPair(input="param_in2", output="param_out1"),
                ParamPair(input="param_in1", output="param_out2"),
                ParamPair(input="param_in2", output="param_out2"),
            ],
            id="No overrides specified",
        ),
        param(
            DemandExecutionParameters(
                command=[],
                inputs=["param_in1", "param_in2"],
                params={
                    "param_with_ref": "${param_out2}",
                    "param_with_refs": "${param_out1}_bar_${param_no_ref}",
                    "param_no_ref": "qaz",
                    "param_in1": Resolvable(local="my_path1", remote=S3_URI).to_dict(),
                    "param_in2": Resolvable(local="my_path2", remote=S3_URI).to_dict(),
                    "param_in_with_ref": "${param_in1}/${param_out1}",
                    "param_out1": "foo",
                    "param_out2": "${param_no_ref}_bar",
                    "param_out3": "${param_no_ref}",
                },
                outputs=["param_out1", "param_out2", "param_out3"],
                output_s3_prefix=S3_URI,
                param_pair_overrides=[
                    ParamPair(input="param_in1", output="param_out1"),
                    ParamSetPair(
                        inputs=frozenset({"param_in1", "param_in2"}),
                        outputs=frozenset({"param_out2", "param_out3"}),
                    ),
                ],
            ),
            [
                ParamSetPair(inputs=frozenset({"param_in1"}), outputs=frozenset({"param_out1"})),
                ParamSetPair(
                    inputs=frozenset({"param_in1", "param_in2"}),
                    outputs=frozenset({"param_out2", "param_out3"}),
                ),
            ],
            [
                ParamPair(input="param_in1", output="param_out1"),
                ParamPair(input="param_in1", output="param_out2"),
                ParamPair(input="param_in2", output="param_out2"),
                ParamPair(input="param_in1", output="param_out3"),
                ParamPair(input="param_in2", output="param_out3"),
            ],
            id="overrides specified",
        ),
    ],
)
def test__DemandExecutionParameters__param_pairs_and_param_set_pairs__work(
    parameters: DemandExecutionParameters,
    expected_param_set_pairs: List[ParamSetPair],
    expected_param_pairs: List[ParamPair],
):
    actual = sorted(parameters.param_set_pairs, key=lambda _: str(_))
    expected = sorted(expected_param_set_pairs, key=lambda _: str(_))
    assert actual == expected

    actual = sorted(parameters.param_pairs, key=lambda _: str(_))
    expected = sorted(expected_param_pairs, key=lambda _: str(_))
    assert actual == expected


def test__add_inputs__redundant_inputs_handled():
    parameters = DemandExecutionParameters(
        params=dict(input1="a", input2="b", input3="c"), inputs=["input2"]
    )

    parameters.add_inputs("input1", "input2", input3="C", input4="D")

    assert parameters.inputs == ["input2", "input1", "input3", "input4"]
    assert parameters.downloadable_job_param_inputs == [
        DownloadableJobParam("input2", mock.ANY, "b"),
        DownloadableJobParam("input1", mock.ANY, "a"),
        DownloadableJobParam("input3", mock.ANY, "C"),
        DownloadableJobParam("input4", mock.ANY, "D"),
    ]


def test__add_outputs__redundant_outputs_handled():
    parameters = DemandExecutionParameters(
        params=dict(output1="a", output2="b", output3="c"),
        outputs=["output2"],
        output_s3_prefix=S3URI("s3://bucket"),
    )

    parameters.add_outputs("output1", "output2", output3="C @ s3://bucket2/C", output4="D")

    assert parameters.outputs == ["output2", "output1", "output3", "output4"]
    assert parameters.uploadable_job_param_outputs == [
        UploadableJobParam("output2", "b", "s3://bucket/b"),
        UploadableJobParam("output1", "a", "s3://bucket/a"),
        UploadableJobParam("output3", "C", "s3://bucket2/C"),
        UploadableJobParam("output4", "D", "s3://bucket/D"),
    ]


def test__get_param__handles_various_inputs():
    parameters = DemandExecutionParameters(
        params={
            "CapitalizedParam": "a",
            "UPPERCASE_PARAM": "b",
            "lowercase_param": "c",
            "hypenated-param": "d",
        }
    )

    assert parameters.get_param("CapitalizedParam") == "a"
    assert parameters.get_param("CAPITALIZEDPARAM") == "a"
    assert parameters.get_param("${CAPITALIZEDPARAM}") == "a"
    assert parameters.get_param("${CapitalizedParam}") == "a"

    assert parameters.get_param("UPPERCASE_PARAM") == "b"
    assert parameters.get_param("uppercase_param") == "b"
    assert parameters.get_param("${uppercase_param}") == "b"
    assert parameters.get_param("${UPPERCASE_PARAM}") == "b"

    assert parameters.get_param("lowercase_param") == "c"
    assert parameters.get_param("LOWERCASE_PARAM") == "c"
    assert parameters.get_param("${LOWERCASE_PARAM}") == "c"
    assert parameters.get_param("${lowercase_param}") == "c"

    assert parameters.get_param("hypenated-param") == "d"
    assert parameters.get_param("HYPENATED_PARAM") == "d"
    assert parameters.get_param("${HYPENATED_PARAM}") == "d"

    assert parameters.get_param("not_a_param") is None


def test__get_job_param__handles_envname_and_name():
    parameters = DemandExecutionParameters(
        params={
            "CapitalizedParam": "a",
            "UPPERCASE_PARAM": "b",
            "lowercase_param": "c",
            "hypenated-param": "d",
        }
    )

    assert parameters.get_job_param("CapitalizedParam") == JobParam("CapitalizedParam", "a")
    assert parameters.get_job_param("CAPITALIZEDPARAM") == JobParam("CapitalizedParam", "a")

    assert parameters.get_job_param("UPPERCASE_PARAM") == JobParam("UPPERCASE_PARAM", "b")
    assert parameters.get_job_param("${uppercase_param}") == JobParam("UPPERCASE_PARAM", "b")

    assert parameters.get_job_param("lowercase_param") == JobParam("lowercase_param", "c")
    assert parameters.get_job_param("LOWERCASE_PARAM") == JobParam("lowercase_param", "c")

    assert parameters.get_job_param("hypenated-param") == JobParam("hypenated-param", "d")
    assert parameters.get_job_param("HYPENATED_PARAM") == JobParam("hypenated-param", "d")


def test__has_param__works():
    parameters = DemandExecutionParameters(
        params={
            "CapitalizedParam": "a",
            "UPPERCASE_PARAM": "b",
            "lowercase_param": "c",
            "hypenated-param": None,
        }
    )

    assert parameters.has_param("CapitalizedParam")
    assert parameters.has_param("CAPITALIZEDPARAM")
    assert parameters.has_param("${CAPITALIZEDPARAM}")
    assert parameters.has_param("${CapitalizedParam}")

    assert parameters.has_param("UPPERCASE_PARAM")
    assert parameters.has_param("uppercase_param")
    assert parameters.has_param("${uppercase_param}")
    assert parameters.has_param("${UPPERCASE_PARAM}")

    assert parameters.has_param("lowercase_param")
    assert parameters.has_param("LOWERCASE_PARAM")
    assert parameters.has_param("${LOWERCASE_PARAM}")
    assert parameters.has_param("${lowercase_param}")

    assert parameters.has_param("hypenated-param")
    assert parameters.has_param("HYPENATED_PARAM")
    assert parameters.has_param("${HYPENATED_PARAM}")

    assert not parameters.has_param("not_a_param")


def test__get_input_job_param__handles_valid_and_missing():
    parameters = DemandExecutionParameters(
        params={
            "param_in": S3_URI,
            "param": "foo",
            "param_out": "bar",
        },
        inputs=["param_in"],
        outputs=["param_out"],
        output_s3_prefix=S3_PREFIX,
    )

    assert parameters.get_input_job_param("param_in") == DownloadableJobParam(
        "param_in", mock.ANY, S3_URI
    )
    assert parameters.get_input_job_param("param") is None
    assert parameters.get_input_job_param("param_out") is None
    assert parameters.get_input_job_param("not_a_param") is None


def test__get_output_job_param__handles_valid_and_missing():
    parameters = DemandExecutionParameters(
        params={
            "param_in": S3_URI,
            "param": "foo",
            "param_out1": "bar",
            "param_out2": {
                "local": "qaz",
                "remote": "s3://bucket/prefix2/qaz",
            },
        },
        inputs=["param_in"],
        outputs=["param_out1", "param_out2"],
        output_s3_prefix=S3_PREFIX,
    )

    assert parameters.get_output_job_param("param_in") is None
    assert parameters.get_output_job_param("param") is None
    assert parameters.get_output_job_param("param_out1") == UploadableJobParam(
        "param_out1", "bar", "s3://bucket/prefix/bar"
    )
    assert parameters.get_output_job_param("param_out2") == UploadableJobParam(
        "param_out2", "qaz", "s3://bucket/prefix2/qaz"
    )
    assert parameters.get_output_job_param("not_a_param") is None


def test__job_param_pairs__work():
    parameters = DemandExecutionParameters(
        params={
            "param_in1": S3_URI + "1",
            "param_in2": S3_URI + "2",
            "param_out1": "foo",
            "param_out2": "bar",
            "param_out3": "qaz",
        },
        inputs=["param_in1", "param_in2"],
        outputs=["param_out1", "param_out2", "param_out3"],
        param_pair_overrides=[
            ParamPair(input="param_in1", output="param_out1"),
            ParamPair(input="param_in2", output="param_out2"),
        ],
        output_s3_prefix=S3_PREFIX,
    )

    IN1 = DownloadableJobParam("param_in1", mock.ANY, S3_URI + "1")
    IN2 = DownloadableJobParam("param_in2", mock.ANY, S3_URI + "2")
    OUT1 = UploadableJobParam("param_out1", "foo", S3_PREFIX / "foo")
    OUT2 = UploadableJobParam("param_out2", "bar", S3_PREFIX / "bar")
    OUT3 = UploadableJobParam("param_out3", "qaz", S3_PREFIX / "qaz")

    actual = sorted(
        parameters.job_param_pairs,
        key=lambda _: (_.output.name if _.output else "", _.input.name if _.input else ""),
    )
    expected = [
        JobParamPair(IN1, OUT1),
        JobParamPair(IN2, OUT2),
        JobParamPair(IN1, OUT3),
        JobParamPair(IN2, OUT3),
    ]

    assert actual == expected


def test__job_param_set_pairs__work():
    parameters = DemandExecutionParameters(
        params={
            "param_in1": S3_URI + "1",
            "param_in2": S3_URI + "2",
            "param_out1": "foo",
            "param_out2": "bar",
            "param_out3": "qaz",
        },
        inputs=["param_in1", "param_in2"],
        outputs=["param_out1", "param_out2", "param_out3"],
        param_pair_overrides=[
            ParamPair(input="param_in1", output="param_out1"),
            ParamPair(input="param_in2", output="param_out2"),
        ],
        output_s3_prefix=S3_PREFIX,
    )

    IN1 = DownloadableJobParam("param_in1", "tmpe2cbd6f1", S3_URI + "1")
    IN2 = DownloadableJobParam("param_in2", "tmpde6f6a9e", S3_URI + "2")
    OUT1 = UploadableJobParam("param_out1", "foo", S3_PREFIX / "foo")
    OUT2 = UploadableJobParam("param_out2", "bar", S3_PREFIX / "bar")
    OUT3 = UploadableJobParam("param_out3", "qaz", S3_PREFIX / "qaz")

    actual = parameters.job_param_set_pairs
    expected = [
        JobParamSetPair({IN1, IN2}, {OUT3}),
        JobParamSetPair({IN1}, {OUT1}),
        JobParamSetPair({IN2}, {OUT2}),
    ]

    assert actual == expected


def test__error_if_outputs_and_no_output_s3_prefix():
    with raises(ValueError):
        DemandExecutionParameters(
            params={
                "param_in": S3_URI,
                "param": "foo",
                "param_out": "bar",
            },
            inputs=["param_in"],
            outputs=["param_out"],
        )
