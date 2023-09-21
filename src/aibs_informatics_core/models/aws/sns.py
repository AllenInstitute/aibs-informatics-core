import re
from typing import ClassVar, Pattern

from aibs_informatics_core.collections import ValidatedStr


class SNSTopicArn(ValidatedStr):
    """ARN for AWS SNS Topic

    Examples:
        arn:aws:sns:us-west-2:123456789012:MyTopic
            region: us-west-2
            account: 123456789012
            topic: MyTopic

    """

    regex_pattern: ClassVar[Pattern] = re.compile(
        r"arn:aws:sns:([\w-]*):([\d]{12}):[\w\-\_]+(?:\.fifo)?"
    )
