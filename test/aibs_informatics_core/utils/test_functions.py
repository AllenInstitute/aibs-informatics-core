from pytest import mark, param

from aibs_informatics_core.utils.functions import (
    filter_kwargs,
    get_callable_params,
)

# ---------------------------------------------------------------------------
# Helpers for get_callable_params / filter_kwargs tests
# ---------------------------------------------------------------------------


def _func_no_args():
    pass


def _func_positional_only(a, b, /):
    pass


def _func_regular(name: str, greeting: str = "Hello"):
    pass


def _func_with_var_keyword(name: str, **kwargs):
    pass


def _func_with_var_positional(name: str, *args, flag: bool = False):
    pass


def _func_mixed(a, /, b, *args, c=1, **kwargs):
    pass


class _CallableClass:
    def __init__(self, x: int, y: int = 0):
        pass


class _CallableClassVarKw:
    def __init__(self, x: int, **kwargs):
        pass


class _CallableObj:
    def __call__(self, z: str):
        pass


# ---------------------------------------------------------------------------
# get_callable_params tests
# ---------------------------------------------------------------------------


@mark.parametrize(
    "func, include_var_keyword, expected",
    [
        param(_func_no_args, False, set(), id="no args"),
        param(_func_positional_only, False, {"a", "b"}, id="positional only"),
        param(_func_regular, False, {"name", "greeting"}, id="regular params"),
        param(
            _func_with_var_keyword,
            False,
            {"name"},
            id="var keyword ignored",
        ),
        param(
            _func_with_var_keyword,
            True,
            set(),
            id="var keyword sentinel",
        ),
        param(
            _func_with_var_positional,
            False,
            {"name", "flag"},
            id="var positional ignored, kw-only kept",
        ),
        param(
            _func_mixed,
            False,
            {"a", "b", "c"},
            id="mixed params, no var keyword",
        ),
        param(
            _func_mixed,
            True,
            set(),
            id="mixed params, var keyword sentinel",
        ),
        param(
            _CallableClass,
            False,
            {"x", "y"},
            id="class __init__",
        ),
        param(
            _CallableClass,
            True,
            {"x", "y"},
            id="class __init__ no var kw",
        ),
        param(
            _CallableClassVarKw,
            True,
            set(),
            id="class __init__ with var kw sentinel",
        ),
    ],
)
def test__get_callable_params(func, include_var_keyword, expected):
    assert get_callable_params(func, include_var_keyword=include_var_keyword) == expected


# ---------------------------------------------------------------------------
# filter_kwargs tests
# ---------------------------------------------------------------------------


@mark.parametrize(
    "func, kwargs, expected",
    [
        param(
            _func_regular,
            {"name": "World", "greeting": "Hi", "extra": 42},
            {"name": "World", "greeting": "Hi"},
            id="filters extra keys",
        ),
        param(
            _func_regular,
            {"name": "World"},
            {"name": "World"},
            id="subset of params",
        ),
        param(
            _func_regular,
            {},
            {},
            id="empty kwargs",
        ),
        param(
            _func_with_var_keyword,
            {"name": "x", "anything": 1, "other": 2},
            {"name": "x", "anything": 1, "other": 2},
            id="var keyword passes everything",
        ),
        param(
            _CallableClass,
            {"x": 1, "y": 2, "z": 3},
            {"x": 1, "y": 2},
            id="class constructor filters",
        ),
        param(
            _func_with_var_positional,
            {"name": "a", "flag": True, "nope": 0},
            {"name": "a", "flag": True},
            id="kw-only kept, extra filtered",
        ),
    ],
)
def test__filter_kwargs(func, kwargs, expected):
    assert filter_kwargs(func, kwargs) == expected
