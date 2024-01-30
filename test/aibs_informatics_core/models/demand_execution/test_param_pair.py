from pytest import mark, param

from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.demand_execution.job_param import (
    DownloadableJobParam,
    UploadableJobParam,
)
from aibs_informatics_core.models.demand_execution.param_pair import (
    JobParamPair,
    JobParamSetPair,
    ParamPair,
    ParamSetPair,
    ResolvedParamSetPair,
)
from aibs_informatics_core.models.unique_ids import UniqueID


@mark.parametrize(
    "inputs, outputs, expected",
    [
        param([], [], [], id="no input and no output"),
        param(
            ["i1"],
            ["o1"],
            [
                ParamPair("i1", "o1"),
            ],
            id="single input and output",
        ),
        param(
            ["i1", "i2"],
            [],
            [
                ParamPair("i1", None),
                ParamPair("i2", None),
            ],
            id="multiple inputs and no outputs",
        ),
        param(
            [],
            ["o1", "o2"],
            [
                ParamPair(None, "o1"),
                ParamPair(None, "o2"),
            ],
            id="no inputs and multiple outputs",
        ),
        param(
            ["i1", "i2"],
            ["o1", "o2"],
            [
                ParamPair("i1", "o1"),
                ParamPair("i1", "o2"),
                ParamPair("i2", "o1"),
                ParamPair("i2", "o2"),
            ],
            id="multi inputs and outputs",
        ),
    ],
)
def test__ParamPair__from_sets__works(inputs, outputs, expected):
    actual = ParamPair.from_sets(inputs=inputs, outputs=outputs)
    assert actual == expected


@mark.parametrize(
    "set_pairs, expected",
    [
        param(
            [
                ParamSetPair({"i1"}, {"o1"}),
                ParamSetPair({"i2"}, {"o2"}),
            ],
            [
                ParamPair("i1", "o1"),
                ParamPair("i2", "o2"),
            ],
            id="single input and output",
        ),
    ],
)
def test__ParamPair__from_set_pairs__works(set_pairs, expected):
    actual = ParamPair.from_set_pairs(*set_pairs)
    assert actual == expected


@mark.parametrize(
    "pairs, expected",
    [
        param(
            [
                ParamPair("i1", "o1"),
                ParamPair("i2", "o2"),
            ],
            [
                ParamSetPair({"i1"}, {"o1"}),
                ParamSetPair({"i2"}, {"o2"}),
            ],
            id="single input and output",
        ),
        param(
            [
                ParamPair("i1", "o1"),
                ParamPair("i1", "o2"),
                ParamPair("i2", "o1"),
                ParamPair("i2", "o2"),
            ],
            [
                ParamSetPair({"i1", "i2"}, {"o1"}),
                ParamSetPair({"i1", "i2"}, {"o2"}),
            ],
            id="multiple outputs separated",
        ),
        param(
            [
                ParamPair(None, "o1"),
                ParamPair(None, "o2"),
                ParamPair("i2", "o2"),
                ParamPair("i1", None),
                ParamPair("i2", None),
            ],
            [
                ParamSetPair({}, {"o1"}),
                ParamSetPair({"i2"}, {"o2"}),
                ParamSetPair({"i1", "i2"}, {}),
            ],
            id="null inputs and outputs handled",
        ),
    ],
)
def test__ParamSetPair__from_pairs__works(pairs, expected):
    actual = ParamSetPair.from_pairs(*pairs)
    assert actual == expected


INP1 = DownloadableJobParam("input1", "local_value1", S3URI("s3://any-bucket/any-key"))
INP2 = DownloadableJobParam("input2", "local_value2", S3URI("s3://another-bucket/another-key"))
INP3 = DownloadableJobParam("input3", "local_value3", UniqueID.create("i3"))
INP3 = DownloadableJobParam("input3", "local_value3", UniqueID.create("i4"))

OUT1 = UploadableJobParam("output1", "local_output1", UniqueID.create("o1"))
OUT2 = UploadableJobParam("output2", "local_output2", UniqueID.create("o2"))
OUT3 = UploadableJobParam("output3", "local_output3", S3URI("s3://another-bucket/a-third-key"))
OUT4 = UploadableJobParam("output4", "local_output4", UniqueID.create("o4"))


@mark.parametrize(
    "inputs, outputs, expected",
    [
        param([], [], [], id="no input and no output"),
        param(
            [INP1],
            [OUT1],
            [
                JobParamPair(INP1, OUT1),
            ],
            id="single input and output",
        ),
        param(
            [INP1, INP2],
            [],
            [
                JobParamPair(INP1, None),
                JobParamPair(INP2, None),
            ],
            id="multiple inputs and no outputs",
        ),
        param(
            [],
            [OUT1, OUT2],
            [
                JobParamPair(None, OUT1),
                JobParamPair(None, OUT2),
            ],
            id="no inputs and multiple outputs",
        ),
        param(
            [INP1, INP2],
            [OUT1, OUT2],
            [
                JobParamPair(INP1, OUT1),
                JobParamPair(INP1, OUT2),
                JobParamPair(INP2, OUT1),
                JobParamPair(INP2, OUT2),
            ],
            id="multi inputs and outputs",
        ),
    ],
)
def test__JobParamPair__from_sets__works(inputs, outputs, expected):
    actual = JobParamPair.from_sets(inputs=inputs, outputs=outputs)
    assert actual == expected


@mark.parametrize(
    "set_pairs, expected",
    [
        param(
            [
                JobParamSetPair({INP1}, {OUT1}),
                JobParamSetPair({INP2}, {OUT2}),
            ],
            [
                JobParamPair(INP1, OUT1),
                JobParamPair(INP2, OUT2),
            ],
            id="single input and output",
        ),
    ],
)
def test__JobParamPair__from_set_pairs__works(set_pairs, expected):
    actual = JobParamPair.from_set_pairs(*set_pairs)
    assert actual == expected


@mark.parametrize(
    "pairs, expected",
    [
        param(
            [
                JobParamPair(INP1, OUT3),
                JobParamPair(INP1, OUT4),
                JobParamPair(INP2, OUT3),
                JobParamPair(INP2, OUT4),
            ],
            [
                JobParamSetPair({INP1, INP2}, {OUT3}),
                JobParamSetPair({INP1, INP2}, {OUT4}),
            ],
            id="inputs merged, but outputs are not",
        ),
    ],
)
def test__JobParamSetPair__from_pairs__works(pairs, expected):
    actual = JobParamSetPair.from_pairs(*pairs)
    assert actual == expected


def test__ParamSetPairs__add_inputs__remove_inputs():
    p = ParamSetPair({"i1"}, {"o1"})
    p.add_inputs("i2")
    assert p.inputs == {"i1", "i2"}
    p.add_inputs("i1")
    assert p.inputs == {"i1", "i2"}
    p.remove_inputs("i2")
    assert p.inputs == {"i1"}
    p.remove_inputs("i3")
    assert p.inputs == {"i1"}


def test__ParamSetPairs__add_outputs__remove_outputs():
    p = ParamSetPair({"i1"}, {"o1"})
    p.add_outputs("o2")
    assert p.outputs == {"o1", "o2"}
    p.add_outputs("o1")
    assert p.outputs == {"o1", "o2"}
    p.remove_outputs("o2")
    assert p.outputs == {"o1"}
    p.remove_outputs("o3")
    assert p.outputs == {"o1"}


def test__JobParamSetPairs__add_inputs__remove_inputs():
    p = JobParamSetPair({INP1}, {OUT1})
    p.add_inputs(INP2)
    assert p.inputs == {INP1, INP2}
    p.add_inputs(INP1)
    assert p.inputs == {INP1, INP2}
    p.remove_inputs(INP2)
    assert p.inputs == {INP1}
    p.remove_inputs(INP3)
    assert p.inputs == {INP1}


def test__JobParamSetPairs__add_outputs__remove_outputs():
    p = JobParamSetPair({INP1}, {OUT1})
    p.add_outputs(OUT2)
    assert p.outputs == {OUT1, OUT2}
    p.add_outputs(OUT1)
    assert p.outputs == {OUT1, OUT2}
    p.remove_outputs(OUT2)
    assert p.outputs == {OUT1}
    p.remove_outputs(OUT3)
    assert p.outputs == {OUT1}


def test__ResolvedParamSetPair__to_dict():
    r1 = S3URI("s3://any-bucket/any-key")
    r2 = S3URI("s3://another-bucket/another-key")

    p = ResolvedParamSetPair({r1}, {r2})
    assert p.to_dict() == {"inputs": [r1], "outputs": [r2]}


def test__ResolvedParamSetPair__from_dict():
    r1 = S3URI("s3://any-bucket/any-key")
    r2 = S3URI("s3://another-bucket/another-key")

    p = ResolvedParamSetPair.from_dict({"inputs": [r1], "outputs": [r2]})
    assert p.inputs == frozenset({r1})
    assert p.outputs == frozenset({r2})
