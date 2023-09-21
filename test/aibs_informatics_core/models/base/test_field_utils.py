from dataclasses import dataclass, fields
from typing import Optional, Union

import pytest

from aibs_informatics_core.models.base import FieldProps, SchemaModel


@dataclass
class YetAnotherDC(SchemaModel):
    req: str
    opt: Optional[str]
    another_opt: Union[int, Union[Optional[int], bool]]
    opt_with_default: Optional[str] = None
    non_opt_with_default: str = "empty_sm"


@pytest.mark.parametrize(
    "cls_field, expected",
    list(zip(fields(YetAnotherDC), [True, True, True, False, False])),
)
def test__FieldProps__requires_init_and_has_default(cls_field, expected):
    assert FieldProps(cls_field).requires_init() == expected
    assert FieldProps(cls_field).has_default() != expected


@pytest.mark.parametrize(
    "cls_field, expected",
    list(zip(fields(YetAnotherDC), [False, True, True, True, False])),
)
def test__FieldProps__is_optional_type(cls_field, expected):
    assert FieldProps(cls_field).is_optional_type() == expected
