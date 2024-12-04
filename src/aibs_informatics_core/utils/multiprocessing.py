__all__ = [
    "parallel_starmap",
    "starmap_with_kwargs",
    "apply_args_and_kwargs",
]

from itertools import repeat
from multiprocessing import pool as mp_pool
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Type, TypeVar, Union

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
    fn: Callable[[List[Any]], U],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
) -> U:
    return fn(*args, **kwargs)  # type: ignore  # pragma: no cover


def parallel_starmap(
    callable: Callable[[Any], U],
    arguments: Sequence[T],
    keyword_arguments: Optional[Union[Sequence[Mapping[str, Any]], Mapping[str, Any]]] = None,
    pool_class: Optional[Type[mp_pool.Pool]] = None,
    processes: Optional[int] = None,
    chunk_size: Optional[int] = None,
    callback: Optional[Callable[[List[T]], Any]] = None,
    error_callback: Optional[Callable[[BaseException], None]] = None,
) -> List[U]:
    pool_class = pool_class or mp_pool.Pool
    with pool_class(processes=processes) as pool:
        starmap_arguments = zip(
            repeat(callable),
            arguments,
            repeat(keyword_arguments or {})
            if not isinstance(keyword_arguments, Sequence)
            else keyword_arguments,
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
