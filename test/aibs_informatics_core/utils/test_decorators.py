import warnings

from pytest import raises

from aibs_informatics_core.utils.decorators import deprecated, retry

MILLISEC = 0.001


def test__retry__calls_three_times():
    call_count = 0

    @retry(Exception, tries=3, delay=0.01, backoff=2)
    def my_func():
        nonlocal call_count
        call_count += 1
        raise Exception("foo")

    with raises(Exception):
        my_func()

    assert call_count == 3


def test__retry__handles_select():
    call_count = 0

    @retry((ValueError,), tries=3, delay=0.01, backoff=2)
    def my_func(x: int):
        nonlocal call_count
        call_count += 1
        if x + call_count < 2:
            raise ValueError("foo")
        elif x + call_count > 20:
            raise TypeError("foo")
        return x + call_count

    with raises(TypeError):
        my_func(20)
    assert call_count == 1

    call_count = 0
    my_func(0)
    assert call_count == 2


def test__retry__handles_callback():
    call_count = 0

    @retry(
        Exception,
        tries=3,
        delay=0.01,
        backoff=2,
        retryable_exception_callbacks=[lambda e: e.args[0] == "foo"],
    )
    def my_func():
        nonlocal call_count
        call_count += 1
        raise Exception("foo")

    with raises(Exception):
        my_func()

    assert call_count == 3


def test__deprecated__warns():
    @deprecated("foo")
    def my_func():
        pass

    with warnings.catch_warnings(record=True) as w:
        my_func()
        assert len(w) == 1
        assert issubclass(w[-1].category, PendingDeprecationWarning)
        assert "foo" in str(w[-1].message)
