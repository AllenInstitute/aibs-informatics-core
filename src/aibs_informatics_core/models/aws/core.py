import re
from typing import ClassVar

from aibs_informatics_core.collections import ValidatedStr

AWS_REGION_PATTERN_STR = (
    r"(?:us(?:-gov)?|ap|ca|cn|eu|sa)-(?:central|(?:north|south)?(?:east|west)?)-(?:\d)"
)
AWS_REGION_PATTERN = re.compile(AWS_REGION_PATTERN_STR)

AWS_ACCOUNT_PATTERN_STR = r"[\d]{10,12}"
AWS_ACCOUNT_PATTERN = re.compile(AWS_ACCOUNT_PATTERN_STR)


class AWSAccountId(ValidatedStr):
    regex_pattern: ClassVar[re.Pattern] = AWS_ACCOUNT_PATTERN


class AWSRegion(ValidatedStr):
    regex_pattern: ClassVar[re.Pattern] = AWS_REGION_PATTERN
