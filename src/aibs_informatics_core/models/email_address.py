import re
from typing import ClassVar, Pattern

from aibs_informatics_core.collections import ValidatedStr


class EmailAddress(ValidatedStr):
    """Simple Email Address Validation

    No whitespaces, has an @
    """

    regex_pattern: ClassVar[Pattern] = re.compile(r"\S+@\S+")
