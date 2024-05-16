__all__ = [
    "cache",
    "cached_property",
    "deprecated",
    "retry",
]

import logging
import time
import warnings
from functools import cache, cached_property, wraps
from typing import Callable, List, Optional, Tuple, Type, Union

ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]
ExceptionCallbackType = Callable[[Exception], bool]


def retry(
    retryable_exceptions: ExceptionTypes,
    retryable_exception_callbacks: Optional[
        List[Union[ExceptionCallbackType, Tuple[Type[Exception], ExceptionCallbackType]]]
    ] = None,
    tries: int = 4,
    delay: float = 3,
    backoff: float = 2,
    logger: Optional[logging.Logger] = None,
):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry


    Args:
        retryable_exceptions (Exception, tuple): One or more exception classes to retry on. May
            be a single exception class or tuple of exceptions classes to check.
        retryable_exception_callbacks (Optional,[Callable[[Exception], bool]]): Optional callback
            function to inspect retryable exceptions. If returns False, the exception is raised.
        tries (int): number of times to try (not retry) before giving up
        delay (int, float): initial delay between retries in seconds
        backoff (int): backoff multiplier e.g. value of 2 will double the delay each retry
        logger (logging.Logger): logger to use. The default logger runs in the decorators
                                 namespace, but this can be overridden by passing one in.

    Returns:
        decorated function
    """
    logger = logger or logging.getLogger(__name__)

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except retryable_exceptions as ex:
                    applicable_callbacks = [
                        callback
                        for type_ex, callback in [
                            (None, _) if not isinstance(_, tuple) else _
                            for _ in retryable_exception_callbacks or []
                        ]
                        if not type_ex or issubclass(type(ex), type_ex)
                    ]

                    # Raise exception if
                    # 1. There are applicable callbacks
                    # 2. no callbacks return true
                    if applicable_callbacks and not any(
                        [callback(ex) for callback in applicable_callbacks]
                    ):
                        raise ex
                    assert logger is not None
                    logger.warning("%s, Retrying in %d seconds..." % (str(ex), mdelay))
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def deprecated(msg, klass=PendingDeprecationWarning):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(msg, klass, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
