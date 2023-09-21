__all__ = ["StateMachineArn", "ExecutionArn"]

import re

from aibs_informatics_core.collections import ValidatedStr


class StateMachineArn(ValidatedStr):
    """ARN for AWS Step Function State Machine

    Examples:
        arn:aws:states:us-west-2:123456789012:stateMachine:dev-my-state-machine
            region: us-west-2
            account_id: 123456789012
            state_machine_name: dev-my-state-machine
    """

    regex_pattern = re.compile(r"arn:aws:states:([\w-]*):([\d]{12}):stateMachine:([\w_-]+)")

    @property
    def region(self):
        return self.get_match_groups()[0]

    @property
    def account_id(self):
        return self.get_match_groups()[1]

    @property
    def state_machine_name(self):
        return self.get_match_groups()[2]


class ExecutionArn(StateMachineArn):
    """ARN for AWS Step Function State Machine execution

    Examples:
        arn:aws:states:us-west-2:123456789012:execution:dev-my-state-machine:37dc395b-01d6-41c7-a665-b9fe422996f9
            region: us-west-2
            account_id: 123456789012
            state_machine_name: dev-my-state-machine
            execution_name: 37dc395b-01d6-41c7-a665-b9fe422996f9
    """

    regex_pattern = re.compile(r"arn:aws:states:([\w-]*):([\d]{12}):execution:([\w_-]+):([\w_-]+)")

    @property
    def execution_name(self) -> str:
        return self.get_match_groups()[3]  # type: ignore
