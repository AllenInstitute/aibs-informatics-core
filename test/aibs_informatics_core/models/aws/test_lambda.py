from aibs_informatics_test_resources import does_not_raise
from pytest import mark, param, raises

from aibs_informatics_core.models.aws.lambda_ import LambdaFunctionName


@mark.parametrize(
    "value, expected_name, expected_account, expected_region, expected_version, raise_expectation",
    [
        param(
            "arn::lambda:us-west-2:12345678901:function:my-function:$LATEST",
            "my-function",
            "12345678901",
            "us-west-2",
            "$LATEST",
            does_not_raise(),
            id="full",
        ),
        param(
            "arn::lambda:us-west-2:12345678901:function:my-function",
            "my-function",
            "12345678901",
            "us-west-2",
            None,
            does_not_raise(),
            id="full no version",
        ),
        param(
            "arn::lambda:us-west-2:12345678901:function:my-function:1",
            "my-function",
            "12345678901",
            "us-west-2",
            "1",
            does_not_raise(),
            id="full with version",
        ),
        param(
            "us-west-2:1234567890:function:my-function:1",
            "my-function",
            "1234567890",
            "us-west-2",
            "1",
            does_not_raise(),
            id="partial arn with region, account id",
        ),
        param(
            "1234567890:function:my-function:1",
            "my-function",
            "1234567890",
            None,
            "1",
            does_not_raise(),
            id="partial arn with account id",
        ),
        param(
            "function:my-function:1",
            "my-function",
            None,
            None,
            "1",
            does_not_raise(),
            id="partial arn",
        ),
        param(
            "function:my-function",
            "my-function",
            None,
            None,
            None,
            does_not_raise(),
            id="partial arn no version",
        ),
        param(
            "function-name", "function-name", None, None, None, does_not_raise(), id="name only"
        ),
        param(
            "arn:aws:lambda:1234567890:us-west-2:swap",
            None,
            None,
            None,
            None,
            raises(ValueError),
            id="invalid arn",
        ),
        param(
            "arn::lambda:us-west-2:12345678901:function",
            None,
            None,
            None,
            None,
            raises(ValueError),
            id="missing function name",
        ),
        param(
            "arn::lambda:us-west-2:12345678901:function:",
            None,
            None,
            None,
            None,
            raises(ValueError),
            id="empty function name",
        ),
    ],
)
def test__AWSAccountId__validation(
    value, expected_name, expected_account, expected_region, expected_version, raise_expectation
):
    with raise_expectation:
        function_name = LambdaFunctionName(value)

    if expected_name:
        assert function_name.function_name == expected_name
        assert function_name.account_id == expected_account
        assert function_name.region == expected_region
        assert function_name.version == expected_version
