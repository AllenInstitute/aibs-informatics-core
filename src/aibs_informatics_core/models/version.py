import re
from dataclasses import dataclass
from functools import total_ordering
from typing import ClassVar, Optional, Pattern

from aibs_informatics_core.collections import ValidatedStr


@total_ordering
@dataclass
class Version:
    major_version: int
    minor_version: Optional[int] = None
    revision: Optional[int] = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Version):
            return (self.major_version, self.minor_version or -1, self.revision or -1) == (
                other.major_version,
                other.minor_version or -1,
                other.revision or -1,
            )
        elif isinstance(other, VersionStr):
            return self == other.version
        else:
            return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Version):
            return (self.major_version, self.minor_version or -1, self.revision or -1) < (
                other.major_version,
                other.minor_version or -1,
                other.revision or -1,
            )
        elif isinstance(other, VersionStr):
            return self < other.version
        else:
            return NotImplemented


class VersionStr(ValidatedStr):

    """Version String

    Version String      Major   Minor   Revision
    --------------   ------------------------------
        1.0.0             1       0        0
        1.0.*             1       0       any
        1.0               1       0       any
        1.*               1      any      any
        1                 1      any      any


    """

    regex_pattern: ClassVar[Pattern] = re.compile(r"(?:v?)(?:(\d+))(?:\.(\d+))?(?:\.(\*|\d+))?")

    @property
    def version(self) -> Version:
        major_str, minor_str, revision_str = self.get_match_groups()
        return Version(
            major_version=int(major_str),
            minor_version=int(minor_str) if minor_str and minor_str != "*" else None,
            revision=int(revision_str) if revision_str and revision_str != "*" else None,
        )

    @property
    def major_version(self) -> int:
        return self.version.major_version

    @property
    def minor_version(self) -> Optional[int]:
        return self.version.minor_version

    @property
    def revision(self) -> Optional[int]:
        return self.version.revision

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Version):
            return self.version == other
        elif isinstance(other, VersionStr):
            return self.version == other.version
        elif isinstance(other, str):
            try:
                other = VersionStr(other)
            except ValueError:
                return False
            else:
                return self == other
        else:
            return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Version):
            return self.version < other
        elif isinstance(other, VersionStr):
            return self.version < other.version
        else:
            return NotImplemented
