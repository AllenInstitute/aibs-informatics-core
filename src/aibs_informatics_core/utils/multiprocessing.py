__all__ = [
    "parallel_starmap",
    "starmap_with_kwargs",
    "apply_args_and_kwargs",
]

from collections.abc import Callable, Iterable, Mapping, Sequence
from itertools import repeat
from multiprocessing import pool as mp_pool
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")

POOL = TypeVar("POOL", bound=mp_pool.Pool)


def starmap_with_kwargs(
    pool,
    fn: Callable,
    args_iter: Sequence[Iterable[Any]],
    kwargs_iter: Sequence[Mapping[str, Any]],
):
    args_for_starmap = zip(repeat(fn), args_iter, kwargs_iter)
    return pool.starmap(apply_args_and_kwargs, args_for_starmap)


def apply_args_and_kwargs(fn, args: Iterable[Any], kwargs: Mapping[str, Any]):
    return fn(*args, **kwargs)  # pragma: no cover


def _starmap_apply(
    fn: Callable[[list[Any]], U],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
) -> U:
    return fn(*args, **kwargs)  # type: ignore  # pragma: no cover


def parallel_starmap(
    callable: Callable[[Any], U],
    arguments: Sequence[T],
    keyword_arguments: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    pool_class: type[mp_pool.Pool] | None = None,
    processes: int | None = None,
    chunk_size: int | None = None,
    callback: Callable[[list[T]], Any] | None = None,
    error_callback: Callable[[BaseException], None] | None = None,
) -> list[U]:
    pool_class = pool_class or mp_pool.Pool
    with pool_class(processes=processes) as pool:
        starmap_arguments = zip(
            repeat(callable),
            arguments,
            (
                repeat(keyword_arguments or {})
                if not isinstance(keyword_arguments, Sequence)
                else keyword_arguments
            ),
        )

        async_results = [
            pool.starmap_async(
                _starmap_apply,
                (_,),
                chunksize=chunk_size,
                callback=callback,
                error_callback=error_callback,
            )
            for _ in starmap_arguments
        ]

        return [result for async_result in async_results for result in async_result.get()]
