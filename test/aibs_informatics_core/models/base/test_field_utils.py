from dataclasses import dataclass, fields
from test.base import BaseTest
from typing import Optional, Union

import marshmallow as mm
import pytest

from aibs_informatics_core.models.base import FieldProps, SchemaModel
from aibs_informatics_core.models.base.field_utils import FieldMetadataBuilder


@dataclass
class YetAnotherDC(SchemaModel):
    req: str
    opt: Optional[str]
    another_opt: Union[int, Union[Optional[int], bool]]
    opt_with_default: Optional[str] = None
    non_opt_with_default: str = "empty_sm"


class FieldMetadataBuilderTests(BaseTest):
    def test__create_encoder_from_mm_field__works(self):
        f = mm.fields.Int()

        encoder = FieldMetadataBuilder.create_encoder_from_mm_field(f)
        assert encoder("1") == 1

    def test__create_decoder_from_mm_field__works(self):
        f = mm.fields.Int()

        decoder = FieldMetadataBuilder.create_decoder_from_mm_field(f)
        assert decoder("1") == 1


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
