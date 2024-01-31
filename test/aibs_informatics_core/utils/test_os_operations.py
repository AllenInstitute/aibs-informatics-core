from test.base import BaseTest

import pytest
from aibs_informatics_test_resources import does_not_raise

from aibs_informatics_core.utils.os_operations import (
    EnvVarCollection,
    EnvVarFormat,
    EnvVarItem,
    env_var_overrides,
    expandvars,
    find_all_paths,
    generate_env_file_content,
    get_env_var,
    order_env_vars,
    to_env_var_dict,
    to_env_var_list,
    write_env_file,
)


class OSOperationsTests(BaseTest):
    def test__find_all_paths__returns_folders_and_files(self):
        root = self.tmp_path()
        (root / "a").mkdir()
        (root / "b").mkdir()
        (root / "a" / "x").touch()
        (root / "a" / "y").touch()
        (root / "b" / "z").touch()

        expected = [
            root / "a",
            root / "b",
            root / "a" / "x",
            root / "a" / "y",
            root / "b" / "z",
        ]
        expected = [str(p) for p in expected]

        actual = find_all_paths(root, include_dirs=True, include_files=True)
        self.assertListEqual(sorted(actual), sorted(expected))

    def test__find_all_paths__returns_folders_or_files(self):
        root = self.tmp_path()
        (root / "a").mkdir()
        (root / "b").mkdir()
        (root / "a" / "x").touch()
        (root / "a" / "y").touch()
        (root / "b" / "z").touch()

        expected_dirs = [
            root / "a",
            root / "b",
        ]
        expected_files = [
            root / "a" / "x",
            root / "a" / "y",
            root / "b" / "z",
        ]
        actual_dirs = find_all_paths(root, include_dirs=True, include_files=False)
        actual_files = find_all_paths(root, include_dirs=False, include_files=True)
        self.assertListEqual(sorted(actual_dirs), sorted([str(p) for p in expected_dirs]))
        self.assertListEqual(sorted(actual_files), sorted([str(p) for p in expected_files]))

    def test__expandvars__expands_env_vars_without_brackets(self):
        self.set_env_vars(("V1", "signal"), ("V2", "the"))
        self.assertEqual(expandvars("$V1 between $V2 noise"), "signal between the noise")

    def test__expandvars__expands_env_vars_with_brackets(self):
        self.set_env_vars(("V1", "between"), ("V2", "the"))
        self.assertEqual(expandvars("signal${V1}${V2}noise"), "signalbetweenthenoise")

    def test__expandvars__fills_missing_vars_with_env(self):
        self.set_env_vars(("V1", "signal"), ("V2", None))
        self.assertEqual(expandvars("$V1 between $V2 noise"), "signal between $V2 noise")

    def test__expandvars__fills_missing_vars_with_override_default(self):
        self.set_env_vars(("V1", "signal"), ("V2", None))
        self.assertEqual(
            expandvars("${V1}between $V2 noise", default="the"),
            "signalbetween the noise",
        )

    def test__expandvars__does_not_expand_values_if_double_escaped(self):
        self.set_env_vars(("V1", "the"))
        self.assertEqual(
            expandvars("signalbetween\\${V1}noise", skip_escaped=True),
            "signalbetween\\${V1}noise",
        )
        self.assertEqual(
            expandvars("signalbetween \\$V1 noise", skip_escaped=True),
            "signalbetween \\$V1 noise",
        )


@pytest.mark.parametrize(
    "key, value, lower, expected",
    [
        ("KEY1", "value1", False, {"Key": "KEY1", "Value": "value1"}),
        ("KEY2", "value2", True, {"key": "KEY2", "value": "value2"}),
    ],
)
def test_env_var_item_to_dict(key, value, lower, expected):
    env_var_item = EnvVarItem(key, value)
    assert env_var_item.to_dict(lower) == expected


@pytest.mark.parametrize("key, value", [("KEY1", "value1"), ("KEY2", "value2")])
def test_env_var_item_to_tuple(key, value):
    env_var_item = EnvVarItem(key, value)
    assert env_var_item.to_tuple() == (key, value)


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (EnvVarItem("KEY1", "value1"), EnvVarItem("KEY1", "value1")),
        (("KEY2", "value2"), EnvVarItem("KEY2", "value2")),
        ({"key": "KEY3", "value": "value3"}, EnvVarItem("KEY3", "value3")),
    ],
)
def test_env_var_item_from_any(input_value, expected):
    assert EnvVarItem.from_any(input_value) == expected


@pytest.mark.parametrize("input_value", [["invalid", "type"], 123, None])
def test_env_var_item_from_any_invalid(input_value):
    with pytest.raises(ValueError):
        EnvVarItem.from_any(input_value)


ANY_ENV_VAR_DICT = {"KEY1": "value1", "KEY2": "${KEY1}value2", "KEY3": "${KEY2}value3"}
ANY_ENV_VAR_LIST__OBJECT = [
    EnvVarItem("KEY1", "value1"),
    EnvVarItem("KEY2", "${KEY1}value2"),
    EnvVarItem("KEY3", "${KEY2}value3"),
]
ANY_ENV_VAR_LIST__TUPLE = [
    ("KEY1", "value1"),
    ("KEY2", "${KEY1}value2"),
    ("KEY3", "${KEY2}value3"),
]
ANY_ENV_VAR_LIST__DICT_LOWER = [
    {"key": "KEY1", "value": "value1"},
    {"key": "KEY2", "value": "${KEY1}value2"},
    {"key": "KEY3", "value": "${KEY2}value3"},
]
ANY_ENV_VAR_LIST__DICT_UPPER = [
    {"Key": "KEY1", "Value": "value1"},
    {"Key": "KEY2", "Value": "${KEY1}value2"},
    {"Key": "KEY3", "Value": "${KEY2}value3"},
]


@pytest.mark.parametrize(
    "env_vars, env_var_format, expected",
    [
        pytest.param(
            ANY_ENV_VAR_DICT,
            None,
            ANY_ENV_VAR_LIST__TUPLE,
            id="dict to tuple list (default)",
        ),
        pytest.param(
            ANY_ENV_VAR_DICT,
            EnvVarFormat.TUPLE,
            ANY_ENV_VAR_LIST__TUPLE,
            id="dict to tuple list (tuple)",
        ),
        pytest.param(
            ANY_ENV_VAR_DICT,
            EnvVarFormat.OBJECT,
            ANY_ENV_VAR_LIST__OBJECT,
            id="dict to tuple list (object)",
        ),
        pytest.param(
            ANY_ENV_VAR_DICT,
            EnvVarFormat.DICT_LOWER,
            ANY_ENV_VAR_LIST__DICT_LOWER,
            id="dict to tuple list (dict_lower)",
        ),
        pytest.param(
            ANY_ENV_VAR_DICT,
            EnvVarFormat.DICT_UPPER,
            ANY_ENV_VAR_LIST__DICT_UPPER,
            id="dict to tuple list (dict_upper)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            None,
            ANY_ENV_VAR_LIST__TUPLE,
            id="tuple list to tuple list (default)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            EnvVarFormat.TUPLE,
            ANY_ENV_VAR_LIST__TUPLE,
            id="tuple list to tuple list (tuple)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            EnvVarFormat.OBJECT,
            ANY_ENV_VAR_LIST__OBJECT,
            id="tuple list to tuple list (object)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            EnvVarFormat.DICT_LOWER,
            ANY_ENV_VAR_LIST__DICT_LOWER,
            id="tuple list to tuple list (dict_lower)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            EnvVarFormat.DICT_UPPER,
            ANY_ENV_VAR_LIST__DICT_UPPER,
            id="tuple list to tuple list (dict_upper)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__OBJECT,
            None,
            ANY_ENV_VAR_LIST__TUPLE,
            id="object list to tuple list (default)",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__OBJECT,
            EnvVarFormat.TUPLE,
            ANY_ENV_VAR_LIST__TUPLE,
            id="object list to tuple list (tuple)",
        ),
    ],
)
def test_to_env_var_list(env_vars, env_var_format, expected):
    if env_var_format:
        assert to_env_var_list(env_vars, env_var_format=env_var_format) == expected
    else:
        assert to_env_var_list(env_vars) == expected


@pytest.mark.parametrize(
    "env_vars, expected",
    [
        pytest.param(
            ANY_ENV_VAR_DICT,
            ANY_ENV_VAR_DICT,
            id="dict to dict",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__TUPLE,
            ANY_ENV_VAR_DICT,
            id="tuple list to dict",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__OBJECT,
            ANY_ENV_VAR_DICT,
            id="object list to dict",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__DICT_LOWER,
            ANY_ENV_VAR_DICT,
            id="dict_lower list to dict",
        ),
        pytest.param(
            ANY_ENV_VAR_LIST__DICT_UPPER,
            ANY_ENV_VAR_DICT,
            id="dict_upper list to dict",
        ),
    ],
)
def test_to_env_var_dict(env_vars, expected):
    assert to_env_var_dict(env_vars) == expected


@pytest.mark.parametrize(
    "env_vars, env_var_format, expected, raise_expectation",
    [
        pytest.param(
            {"A": "a", "B": "b"},
            None,
            [("A", "a"), ("B", "b")],
            does_not_raise(),
            id="normal",
        ),
        pytest.param(
            {
                "A": "${B}",
                "B": "$C$D",
                "C": "C",
                "D": "$C D",
            },
            None,
            [("C", "C"), ("D", "$C D"), ("B", "$C$D"), ("A", "${B}")],
            does_not_raise(),
            id="references work",
        ),
        pytest.param(
            {"A": "${b}", "B": "${a}"},
            None,
            [("A", "${b}"), ("B", "${a}")],
            does_not_raise(),
            id="case sensitive distinction",
        ),
        pytest.param(
            [("A", "$B $C"), ("B", "$C"), ("C", "C")],
            EnvVarFormat.OBJECT,
            [EnvVarItem("C", "C"), EnvVarItem("B", "$C"), EnvVarItem("A", "$B $C")],
            does_not_raise(),
            id="object list to object list",
        ),
        pytest.param(
            {"A": "${B}", "B": "${C}", "C": "${A}"},
            None,
            None,
            pytest.raises(ValueError),
            id="circular reference",
        ),
    ],
)
def test__order_env_vars__works(
    env_vars: EnvVarCollection, env_var_format, expected, raise_expectation
):
    with raise_expectation:
        if env_var_format:
            actual = order_env_vars(env_vars, env_var_format=env_var_format)
        else:
            actual = order_env_vars(env_vars)

    if expected is not None:
        assert actual == expected


def test__generate_env_file_content__works():
    env_vars = {"A": "a", "B": "b"}
    expected = 'export A="a"\nexport B="b"'
    actual = generate_env_file_content(env_vars)
    assert actual == expected


def test__write_env_file__works(tmp_path):
    env_vars = {"A": "a", "B": "b"}
    expected = 'export A="a"\nexport B="b"'
    file_path = tmp_path / "env.sh"
    write_env_file(env_vars, file_path)
    actual = file_path.read_text()
    assert actual == expected


def test__env_var_overrides__handles_multi_format_env_vars(monkeypatch):
    ev1 = EnvVarItem("KEY1", "value1")
    ev2 = EnvVarItem("KEY2", "value2").to_dict(lower=True)
    ev3 = EnvVarItem("KEY3", "value3").to_tuple()

    # Test overrides existing env vars
    monkeypatch.setenv("KEY1", "nada")
    monkeypatch.delenv("KEY2", raising=False)
    monkeypatch.delenv("KEY3", raising=False)

    assert get_env_var("KEY1") == "nada"
    assert get_env_var("KEY2") is None
    assert get_env_var("KEY3") is None

    with env_var_overrides(ev1, ev2, ev3):
        assert get_env_var("KEY1") == "value1"
        assert get_env_var("KEY2") == "value2"
        assert get_env_var("KEY3") == "value3"

    assert get_env_var("KEY1") == "nada"
    assert get_env_var("KEY2") is None
    assert get_env_var("KEY3") is None
