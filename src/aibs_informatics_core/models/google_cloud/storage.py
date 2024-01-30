from __future__ import annotations

import re
import urllib.parse
from typing import ClassVar

from aibs_informatics_core.collections import ValidatedStr


class GCSPath(ValidatedStr):
    regex_pattern: ClassVar[re.Pattern] = re.compile(
        rf"gs:\/\/([a-zA-Z0-9\-\_\.]+)\/([a-zA-Z0-9\-\_\.\/\%]+)"
    )

    @property
    def bucket(self) -> str:
        return self.get_match_groups()[0]

    @property
    def key(self) -> str:
        return self.get_match_groups()[1]

    @classmethod
    def build(cls, bucket: str, key: str) -> GCSPath:
        return cls(f"gs://{bucket}/{urllib.parse.quote(key)}")
