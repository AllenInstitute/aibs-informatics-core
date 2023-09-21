from test.base import does_not_raise
from typing import Optional

from marshmallow import ValidationError
from pytest import mark, param, raises

from aibs_informatics_core.models.aws.dynamodb import (
    AttributeBaseExpression,
    ConditionBaseExpression,
    ConditionBaseExpressionString,
)

condition_base_expression__valid__test_cases = [
    param(
        {
            "format": "{0} {operator} {1}",
            "operator": "=",
            "values": [{"attr_class": "Key", "attr_name": "k1"}, "s1"],
        },
        ConditionBaseExpression(
            format="{0} {operator} {1}",
            operator="=",
            values=[AttributeBaseExpression("Key", "k1"), "s1"],
        ),
        does_not_raise(),
        id="Simple Condition",
    ),
    param(
        {
            "format": "({0} {operator} {1})",
            "operator": "AND",
            "values": [
                {
                    "operator": "=",
                    "format": "{0} {operator} {1}",
                    "values": [{"attr_class": "Key", "attr_name": "k1"}, "s1"],
                },
                {
                    "operator": "<",
                    "format": "{0} {operator} {1}",
                    "values": [{"attr_class": "Attr", "attr_name": "a1"}, 1],
                },
            ],
        },
        ConditionBaseExpression(
            format="({0} {operator} {1})",
            operator="AND",
            values=[
                ConditionBaseExpression(
                    format="{0} {operator} {1}",
                    operator="=",
                    values=[AttributeBaseExpression(attr_class="Key", attr_name="k1"), "s1"],
                ),
                ConditionBaseExpression(
                    format="{0} {operator} {1}",
                    operator="<",
                    values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), 1],
                ),
            ],
        ),
        does_not_raise(),
        id="Nested Condition (AND)",
    ),
]

condition_base_expression__invalid__test_cases__from_dict = [
    param(
        {},
        None,
        raises(ValidationError),
        id="Empty is invalid",
    ),
    param(
        {"format": "format", "operator": ["operator"], "values": []},
        None,
        raises(ValidationError),
        id="Top-level field is invalid",
    ),
]


condition_base_expression__invalid__test_cases__to_dict = [
    param(
        None,
        ConditionBaseExpression(
            format="({0} {operator} {1})",
            operator="AND",
            values=[
                ConditionBaseExpression(
                    format="{0} {operator} {1}",
                    operator=["="],
                    values=[AttributeBaseExpression(attr_class="Key", attr_name="k1"), "s1"],
                ),
                ConditionBaseExpression(
                    format="{0} {operator} {1}",
                    operator="<",
                    values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), 1],
                ),
            ],
        ),
        raises(ValidationError),
        id="Nested Condition is invalid",
    ),
    param(
        None,
        ConditionBaseExpression(
            format=["{0} {operator} {1}"],
            operator="=",
            values=[AttributeBaseExpression(attr_class="Key", attr_name="k1"), "s1"],
        ),
        raises(ValidationError),
        id="Top-level field is invalid",
    ),
]


@mark.parametrize(
    "model_dict, expected, raises_error",
    condition_base_expression__valid__test_cases
    + condition_base_expression__invalid__test_cases__from_dict,
)
def test__ConditionBaseExpression__from_dict(
    model_dict: dict, expected: Optional[ConditionBaseExpression], raises_error
):
    with raises_error:
        actual = ConditionBaseExpression.from_dict(model_dict)

    if expected:
        assert actual == expected


@mark.parametrize(
    "expected, model, raises_error",
    condition_base_expression__valid__test_cases
    + condition_base_expression__invalid__test_cases__to_dict,
)
def test__ConditionBaseExpression__to_dict(
    model: ConditionBaseExpression, expected: Optional[dict], raises_error
):
    with raises_error:
        actual = model.to_dict()
    if expected is not None:
        assert actual == expected


@mark.parametrize(
    "value, is_key, expected, raises_error",
    [
        param(
            "k1=s1",
            True,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Key", attr_name="k1"), "s1"],
            ),
            does_not_raise(),
            id="Converts operator (=) with str (key)",
        ),
        param(
            "k0.k1=s1",
            True,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Key", attr_name="k0.k1"), "s1"],
            ),
            does_not_raise(),
            id="Converts operator (=) with nested name (key)",
        ),
        param(
            "a1=s1",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), "s1"],
            ),
            does_not_raise(),
            id="Converts operator (=) with str (attr)",
        ),
        param(
            "a1=42",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), 42],
            ),
            does_not_raise(),
            id="Converts operator (=) with int value (attr)",
        ),
        param(
            "a1=`42`",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), "42"],
            ),
            does_not_raise(),
            id="Converts operator (=) with `int` value treated as str (attr)",
        ),
        param(
            "a1=-42.0",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), -42.0],
            ),
            does_not_raise(),
            id="Converts operator (=) with negative float value (attr)",
        ),
        param(
            "a1=false",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="=",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), False],
            ),
            does_not_raise(),
            id="Converts operator (=) to bool value (attr)",
        ),
        param(
            "k1 attribute_exists",
            False,
            ConditionBaseExpression(
                format="{operator}({0})",
                operator="attribute_exists",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="k1")],
            ),
            does_not_raise(),
            id="Converts operator (attribute_exists) to expression without value (attr)",
        ),
        param(
            "a1 begins_with abc",
            False,
            ConditionBaseExpression(
                format="{operator}({0}, {1})",
                operator="begins_with",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), "abc"],
            ),
            does_not_raise(),
            id="Converts operator (begins_with) to condition base expr (attr)",
        ),
        param(
            "a1 IN (42, 56)",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="IN",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), [42, 56]],
            ),
            does_not_raise(),
            id="Converts operator (IN) to list (attr)",
        ),
        param(
            "a1 IN (42, `42`)",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="IN",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), [42, "42"]],
            ),
            does_not_raise(),
            id="Converts operator (IN) with escaped nested values to list (attr)",
        ),
        param(
            "a1 IN 42,56.45",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="IN",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), [42, 56.45]],
            ),
            does_not_raise(),
            id="Converts operator (IN) with no parentheses works (attr)",
        ),
        param(
            "a1 IN 42",
            False,
            ConditionBaseExpression(
                format="{0} {operator} {1}",
                operator="IN",
                values=[AttributeBaseExpression(attr_class="Attr", attr_name="a1"), [42]],
            ),
            does_not_raise(),
            id="Converts operator (IN) with single value cast as list",
        ),
    ],
)
def test__ConditionBaseExpressionString__get_condition_expression(
    value: str, is_key: bool, expected: Optional[ConditionBaseExpression], raises_error
):
    with raises_error:
        actual = ConditionBaseExpressionString(value).get_condition_expression(is_key)

    if expected:
        assert actual == expected
