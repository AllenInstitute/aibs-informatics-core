__all__ = [
    "DEFAULT_LOGGING_FORMAT",
    "get_logger",
    "get_formatter",
    "get_stdout_handler",
    "get_all_handlers",
    "check_formatter_equality",
    "check_handler_equality",
    "enable_stdout_logging",
    "LoggingMixin",
]

import logging
import sys

# Unfortunately, cannot import from decorators, because decorators imports from logging.
from functools import cache, cached_property
from typing import List, Optional, Union

DEFAULT_LOGGING_FORMAT = "%(name)s : %(levelname)s : %(asctime)s : %(message)s"


StrOrFormatter = Union[str, logging.Formatter]
StrOrLogger = Union[str, logging.Logger]
LogLevel = Union[str, int]


def get_logger(name: Optional[str] = None):
    return logging.getLogger(name=name)


@cache
def get_formatter(format: StrOrFormatter = DEFAULT_LOGGING_FORMAT) -> logging.Formatter:
    formatter = logging.Formatter(format) if isinstance(format, str) else format
    return formatter


@cache
def get_stdout_handler(
    format: StrOrFormatter = DEFAULT_LOGGING_FORMAT, level: LogLevel = "INFO"
) -> logging.StreamHandler:
    formatter = get_formatter(format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler


def get_all_handlers(logger: logging.Logger) -> List[logging.Handler]:
    handlers: List[logging.Handler] = []
    if logger.handlers:
        handlers.extend(list(logger.handlers))
    while logger.parent:
        logger = logger.parent
        if logger.handlers:
            handlers.extend(list(logger.handlers))
    return handlers


def check_formatter_equality(
    this: Optional[logging.Formatter], other: Optional[logging.Formatter]
) -> bool:
    if this is None and other is None:
        return True
    if this is None or other is None:
        return False
    else:
        return this._fmt == other._fmt and this.datefmt == other.datefmt


def check_handler_equality(this: logging.Handler, other: logging.Handler) -> bool:
    if type(this) != type(other):
        return False
    if this.level != other.level:
        return False
    if this.get_name() != other.get_name():
        return False
    if not check_formatter_equality(this.formatter, other.formatter):
        return False
    return True


def enable_stdout_logging(
    logger: StrOrLogger, format: StrOrFormatter = DEFAULT_LOGGING_FORMAT, level: LogLevel = "INFO"
) -> logging.Logger:
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)

    handler = get_stdout_handler(format=format, level=level)

    if any([check_handler_equality(handler, existing) for existing in get_all_handlers(logger)]):
        return logger

    logger.addHandler(handler)
    return logger


class LoggingMixin(object):
    @cached_property
    def logger(self) -> logging.Logger:
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(name)

    @property
    def log(self) -> logging.Logger:
        return self.logger

    def log_stacktrace(self, message: str, error: BaseException):
        self.logger.error(message)
        self.logger.exception(error)

    def enable_stdout_logging(self):
        enable_stdout_logging(self.logger)
