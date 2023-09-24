import multiprocessing

from aibs_informatics_core.utils.multiprocessing import *


def fn(x, y):
    return x + y


def test__starmap_with_kwargs():
    pool = multiprocessing.Pool()

    args_iter = [(1,), (2,), (3,)]
    kwargs_iter = [{"y": 1}, {"y": 2}, {"y": 3}]
    assert starmap_with_kwargs(pool, fn, args_iter, kwargs_iter) == [2, 4, 6]


def test__parallel_starmap__simple():
    actual = parallel_starmap(fn, [(1,), (2,), (3,)], [dict(y=1), dict(y=2), dict(y=3)])
    assert actual == [2, 4, 6]
