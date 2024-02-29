__all__ = [
    "AttributeBaseExpression",
    "ConditionBaseExpression",
    "ConditionBaseExpressionString",
    "ConditionBaseExpressionOrString",
]

import re
from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional, Pattern, Union, cast

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.base import (
    CustomStringField,
    ListField,
    RawField,
    SchemaModel,
    UnionField,
    custom_field,
)


@dataclass
class AttributeBaseExpression(SchemaModel):
    attr_class: str
    attr_name: Any = custom_field(mm_field=RawField())


@dataclass
class ConditionBaseExpression(SchemaModel):
    format: str = custom_field(mm_field=CustomStringField(str, strict_mode=True))
    operator: str = custom_field(mm_field=CustomStringField(str, strict_mode=True))
    # type: ignore[misc] # https://github.com/python/mypy/issues/731
    values: List[Union["ConditionBaseExpression", AttributeBaseExpression, Any]] = custom_field(
        mm_field=ListField(
            UnionField(
                [
                    (
                        lambda: ConditionBaseExpression,
                        lambda: ConditionBaseExpression.as_mm_field(),
                    ),
                    (AttributeBaseExpression, AttributeBaseExpression.as_mm_field()),
                    ((str, bool, int), RawField()),
                    ((list, set), ListField(RawField())),
                ]
            )
        )
    )


class ConditionBaseExpressionString(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(
        rf"([\w\.]+)(?:( begins_with | contains | NOT | IN |=|<>|<|<=|>|>=)(.+)|( attribute_exists))"
    )

    @property
    def condition_name(self) -> str:
        return self.get_match_groups()[0]

    @property
    def condition_operator(self) -> str:
        return cast(str, self.get_match_groups()[1] or self.get_match_groups()[3]).strip()

    @property
    def condition_format(self) -> str:
        operator = self.condition_operator
        # These mapping can be found here: boto3/dynamodb/conditions.py
        if operator in ["begins_with", "contains"]:
            return "{operator}({0}, {1})"
        elif operator == "attribute_exists":
            return "{operator}({0})"
        else:
            # operator is comparison condition
            return "{0} {operator} {1}"

    @property
    def condition_values(
        self,
    ) -> List[Union[ConditionBaseExpression, AttributeBaseExpression, Any]]:
        condition_values = [AttributeBaseExpression("Attr", self.condition_name)]
        value = self.get_match_groups()[2]

        def resolve(value: Optional[str], is_iterable: bool = False) -> Any:
            is_enclosed = lambda s, b, e: True if len(s) > 1 and (s[0], s[-1]) == (b, e) else False
            if not value:
                if is_iterable:
                    raise ValueError(
                        "IN operator must be followed by comma seperated values "
                        "enclosed in parentheses, e.g.'(optiona, optionb)'"
                    )
                return value
            if is_enclosed(value, "`", "`"):
                return value[1:-1]
            if is_iterable:
                if is_enclosed(value, "(", ")") or is_enclosed(value, "[", "]"):
                    value = value[1:-1]
                return [resolve(_.strip()) for _ in value.split(",")]
            elif value.lower() in ["false", "true"]:
                return value.lower() == "true"
            try:
                return int(value)
            except ValueError:
                pass
            try:
                return float(value)
            except ValueError:
                pass
            return value

        value = resolve(value, self.condition_operator == "IN")
        if value is not None:
            condition_values.append(value)
        return cast(
            List[Union[ConditionBaseExpression, AttributeBaseExpression, Any]], condition_values
        )

    def get_condition_expression(self, is_key: bool) -> ConditionBaseExpression:
        condition_format = self.condition_format
        condition_operator = self.condition_operator
        condition_values = self.condition_values
        if is_key:
            for condition_value in condition_values:
                if isinstance(condition_value, AttributeBaseExpression):
                    condition_value.attr_class = "Key"
        return ConditionBaseExpression(
            format=condition_format, operator=condition_operator, values=condition_values
        )


ConditionBaseExpressionOrString = Union[ConditionBaseExpression, ConditionBaseExpressionString]
