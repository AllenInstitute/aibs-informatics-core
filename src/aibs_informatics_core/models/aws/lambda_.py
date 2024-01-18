import re
from typing import ClassVar, Optional

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.aws.core import (
    AWS_ACCOUNT_PATTERN_STR,
    AWS_REGION_PATTERN_STR,
    AWSAccountId,
    AWSRegion,
)

LAMBDA_FUNCTION_NAME_PATTERN_STR = (
    r"(?:(?:(?:(?:arn:(?:aws[a-zA-Z-]*)?:lambda:)?"
    rf"(?:({AWS_REGION_PATTERN_STR}):)?)?"
    rf"(?:({AWS_ACCOUNT_PATTERN_STR}):)?)?"
    r"(?:function:))?"
    r"([a-zA-Z0-9\-_]{1,64})"
    r"(?::(\$LATEST|[a-zA-Z0-9-_]+))?"
)
LAMBDA_FUNCTION_NAME_PATTERN = re.compile(LAMBDA_FUNCTION_NAME_PATTERN_STR)


class LambdaFunctionName(ValidatedStr):
    regex_pattern: ClassVar[re.Pattern] = LAMBDA_FUNCTION_NAME_PATTERN

    @property
    def region(self) -> Optional[AWSRegion]:
        aws_region = self.get_match_groups()[0]
        return AWSRegion(aws_region) if aws_region else None

    @property
    def account_id(self) -> Optional[AWSAccountId]:
        aws_account_id = self.get_match_groups()[1]
        return AWSAccountId(aws_account_id) if aws_account_id else None

    @property
    def function_name(self) -> str:
        return self.get_match_groups()[2]

    @property
    def version(self) -> Optional[str]:
        return self.get_match_groups()[3]
