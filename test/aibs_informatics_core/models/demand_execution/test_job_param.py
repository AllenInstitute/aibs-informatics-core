from pytest import mark, param, raises

from aibs_informatics_core.models.demand_execution.job_param import JobParam, JobParamRef


@mark.parametrize(
    "name, expected",
    [
        param("param_a", "${PARAM_A}", id="Simple case"),
        param("param-a", "${PARAM_A}", id="Simple case with hyphen"),
    ],
)
def test__JobParam__as_envname_references__works(name, expected):
    actual = JobParam.as_envname_reference(name)
    assert actual == expected


def test__JobParamRef__replace_references__works():
    job_param = JobParam("param_a", "foo_${param_b}")
    replacements = {"PARAM_B": "bar"}
    actual = JobParamRef.replace_references(job_param.value, replacements)
    expected = "foo_bar"
    assert actual == expected


def test__JobParamRef__replace_references__fails_for_missing_ref():
    job_param = JobParam("param_a", "foo_${param_b}")
    replacements = {"param_b": "bar"}
    with raises(ValueError):
        JobParamRef.replace_references(job_param.value, replacements)


def test__JobParamRef__from_name__works():
    actual = JobParamRef.from_name("param_a")
    expected = JobParamRef("${PARAM_A}")
    assert actual == expected


def test__JobParam__envname_reference__works():
    job_param = JobParam("param_a", "foo_${param_b}")
    actual = job_param.envname_reference
    expected = "${PARAM_A}"
    assert actual == expected


def test__JobParam__update_environment__works():
    job_param = JobParam("param_a", "foo")
    environment = {"PARAM_A": "bar"}

    with raises(ValueError):
        job_param.update_environment(environment, overwrite=False)

    job_param.update_environment(environment, overwrite=True)

    assert environment["PARAM_A"] == "foo"


def test__JobParam__find_references__works():
    actual = JobParam("param_a", "foo_${param_b}").find_references()
    expected = [JobParamRef("${param_b}")]
    assert actual == expected

    actual = JobParam("param_a", "foo").find_references()
    expected = []
    assert actual == expected
