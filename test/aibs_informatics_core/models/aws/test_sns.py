from contextlib import nullcontext as does_not_raise

from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.sns import SNSTopicArn


@mark.parametrize(
    "value, raise_expectation",
    [
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic",
            does_not_raise(),
            id="normal",
        ),
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic-test",
            does_not_raise(),
            id="hyphen",
        ),
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic_test",
            does_not_raise(),
            id="underscore",
        ),
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic.fifo",
            does_not_raise(),
            id="fifo",
        ),
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic.test",
            raises(ValidationError),
            id="dot",
        ),
        param(
            "arn:aws:sns:us-west-2:123456789012:MyTopic#",
            raises(ValidationError),
            id="character",
        ),
    ],
)
def test__SNSTopicArn__validates(
    value: str,
    raise_expectation,
):

    with raise_expectation:
        actual = SNSTopicArn(value)
