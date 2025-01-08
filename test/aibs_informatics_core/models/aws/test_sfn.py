from contextlib import nullcontext as does_not_raise
from typing import Tuple

from pytest import mark, param, raises

from aibs_informatics_core.models.aws.sfn import ExecutionArn, StateMachineArn


@mark.parametrize(
    "arn,expected,raises_error",
    [
        param(
            "arn:aws:states:us-west-2:123456789012:stateMachine:sm-name",
            ("us-west-2", "123456789012", "sm-name"),
            does_not_raise(),
            id="happy case",
        ),
        param(
            "arn:aws:states:us-west-2:123456789012:execution:sm-name:exec-id",
            ("", "", ""),
            raises(ValueError),
            id="invalid execution arn",
        ),
        param(
            "arn:aws:states:us-west-2:126789012:stateMachine:sm-name",
            ("", "", ""),
            raises(ValueError),
            id="invalid account",
        ),
        param(
            "arn:aws:states:us-west-2:126789012:stateMachine:sm/name",
            ("", "", ""),
            raises(ValueError),
            id="invalid name",
        ),
    ],
)
def test_StateMachineArn_validation(arn: str, expected: Tuple[str, ...], raises_error):
    region, account, state_machine_name = expected
    with raises_error:
        sm_arn = StateMachineArn(arn)

        assert sm_arn.region == region
        assert sm_arn.account_id == account
        assert sm_arn.state_machine_name == state_machine_name


@mark.parametrize(
    "arn,expected,raises_error",
    [
        param(
            "arn:aws:states:us-west-2:123456789012:execution:sm-name:exec-id",
            ("us-west-2", "123456789012", "sm-name", "exec-id"),
            does_not_raise(),
            id="happy case",
        ),
        param(
            "arn:aws:states:us-west-2:126789012:execution:sm-name:exec-id",
            ("", "", "", ""),
            raises(ValueError),
            id="invalid account",
        ),
        param(
            "arn:aws:states:us-west-2:126789012:execution:sm/name:exec-id",
            ("", "", "", ""),
            raises(ValueError),
            id="invalid name",
        ),
        param(
            "arn:aws:states:us-west-2:126789012:execution:sm-name:exec/id",
            ("", "", "", ""),
            raises(ValueError),
            id="invalid name",
        ),
    ],
)
def test_ExecutionArn_validation(arn: str, expected: Tuple[str, ...], raises_error):
    region, account, state_machine_name, exec_name = expected
    with raises_error:
        exec_arn = ExecutionArn(arn)

        assert exec_arn.region == region
        assert exec_arn.account_id == account
        assert exec_arn.state_machine_name == state_machine_name
        assert exec_arn.execution_name == exec_name
