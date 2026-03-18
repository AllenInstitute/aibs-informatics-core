__all__ = [
    "filter_kwargs",
    "get_callable_params",
]

import inspect
import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def _inspect_callable(func: Callable) -> tuple[frozenset[str], bool]:
    """Cached introspection of a callable's signature.

    Returns:
        A tuple of (named_params, has_var_keyword) where *named_params* is
        a frozenset of all explicitly named parameter names (excluding
        ``*args`` and ``**kwargs``) and *has_var_keyword* indicates whether
        the callable accepts ``**kwargs``.
    """
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        logger.debug("Cannot inspect signature of %r; returning empty set", func)
        return frozenset(), False

    params: set[str] = set()
    has_var_keyword = False
    for name, param in sig.parameters.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            has_var_keyword = True
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            continue
        params.add(name)

    return frozenset(params), has_var_keyword


def get_callable_params(
    func: Callable,
    include_var_keyword: bool = False,
) -> set[str]:
    """Get the set of parameter names accepted by a callable.

    For classes, inspects ``__init__``. Handles regular functions, bound methods,
    classmethods, staticmethods, and other callables with a ``__call__`` method.

    Args:
        func: The callable to inspect (function, method, class, etc.).
        include_var_keyword: If ``True``, returns an empty set when the callable
            accepts ``**kwargs`` (meaning *any* keyword is valid and filtering
            is unnecessary). Defaults to ``False``, which ignores ``**kwargs``
            and returns only the explicitly named parameters.

    Returns:
        A set of parameter name strings. If *include_var_keyword* is ``True``
        and the callable accepts ``**kwargs``, an empty set is returned as a
        sentinel indicating that no filtering should be applied.
    """
    named_params, has_var_keyword = _inspect_callable(func)
    if include_var_keyword and has_var_keyword:
        return set()
    return set(named_params)


def filter_kwargs(
    func: Callable,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Filter a kwargs dict to only the keys accepted by *func*.

    If the callable accepts ``**kwargs``, the original dict is returned
    unmodified because any keyword argument is valid.

    Args:
        func: The callable whose signature determines the allowed keys.
        kwargs: The keyword-argument dict to filter.

    Returns:
        A new dict containing only the entries whose keys match named
        parameters of *func*, or the original *kwargs* when ``**kwargs``
        is present in the signature.

    Example::

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        data = {"name": "World", "greeting": "Hi", "extra": 42}
        filter_kwargs(greet, data)
        # => {"name": "World", "greeting": "Hi"}
    """
    named_params, has_var_keyword = _inspect_callable(func)
    if has_var_keyword:
        return kwargs
    return {k: v for k, v in kwargs.items() if k in named_params}
