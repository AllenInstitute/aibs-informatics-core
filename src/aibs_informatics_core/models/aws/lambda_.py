import re
from typing import ClassVar, Optional
from urllib.parse import parse_qs

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
LAMBDA_FUNCTION_URL_PATTERN_STR = (
    r"https:\/\/([a-zA-Z0-9-]+)\.lambda-url\."
    rf"({AWS_REGION_PATTERN_STR})"
    r"\.on\.aws"
    r"((?:\/[a-zA-Z0-9\._-]*)*)?"
    r"(?:\?(.*))?"
)

LAMBDA_FUNCTION_NAME_PATTERN = re.compile(LAMBDA_FUNCTION_NAME_PATTERN_STR)
LAMBDA_FUNCTION_URL_PATTERN = re.compile(LAMBDA_FUNCTION_URL_PATTERN_STR)


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


class LambdaFunctionUrl(ValidatedStr):
    regex_pattern: ClassVar[re.Pattern] = LAMBDA_FUNCTION_URL_PATTERN

    @property
    def url_id(self) -> str:
        return self.get_match_groups()[0]

    @property
    def region(self) -> AWSRegion:
        aws_region = self.get_match_groups()[1]
        return AWSRegion(aws_region)

    @property
    def raw_path(self) -> Optional[str]:
        return self.get_match_groups()[-2] or None

    @property
    def raw_query(self) -> Optional[str]:
        return self.get_match_groups()[-1]

    @property
    def path(self) -> str:
        return self.raw_path or ""

    @property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(self.raw_query) if self.raw_query else {}

    @property
    def base_url(self) -> str:
        return f"https://{self.url_id}.lambda-url.{self.region}.on.aws"
