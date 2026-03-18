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
from typing import Union

DEFAULT_LOGGING_FORMAT = "%(name)s : %(levelname)s : %(asctime)s : %(message)s"


StrOrFormatter = Union[str, logging.Formatter]
StrOrLogger = Union[str, logging.Logger]
LogLevel = Union[str, int]


def get_logger(name: str | None = None):
    """Get a logger by name.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        A ``logging.Logger`` instance.
    """
    return logging.getLogger(name=name)


@cache
def get_formatter(format: StrOrFormatter = DEFAULT_LOGGING_FORMAT) -> logging.Formatter:
    """Get or create a cached log formatter.

    Args:
        format: Format string or existing Formatter instance.

    Returns:
        A ``logging.Formatter`` instance.
    """
    formatter = logging.Formatter(format) if isinstance(format, str) else format
    return formatter


@cache
def get_stdout_handler(
    format: StrOrFormatter = DEFAULT_LOGGING_FORMAT, level: LogLevel = "INFO"
) -> logging.StreamHandler:
    """Get or create a cached stdout stream handler.

    Args:
        format: Format string or existing Formatter instance.
        level: Logging level for the handler.

    Returns:
        A ``logging.StreamHandler`` writing to stdout.
    """
    formatter = get_formatter(format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler


def get_all_handlers(logger: logging.Logger) -> list[logging.Handler]:
    """Collect all handlers from a logger and its parent chain.

    Args:
        logger: The logger to inspect.

    Returns:
        A list of all handlers attached to the logger and its ancestors.
    """
    handlers: list[logging.Handler] = []
    if logger.handlers:
        handlers.extend(list(logger.handlers))
    while logger.parent:
        logger = logger.parent
        if logger.handlers:
            handlers.extend(list(logger.handlers))
    return handlers


def check_formatter_equality(
    this: logging.Formatter | None, other: logging.Formatter | None
) -> bool:
    """Check if two formatters are equivalent.

    Args:
        this: First formatter (or None).
        other: Second formatter (or None).

    Returns:
        True if both formatters have the same format and datefmt.
    """
    if this is None and other is None:
        return True
    if this is None or other is None:
        return False
    else:
        return this._fmt == other._fmt and this.datefmt == other.datefmt


def check_handler_equality(this: logging.Handler, other: logging.Handler) -> bool:
    """Check if two handlers are equivalent.

    Compares type, level, name, and formatter.

    Args:
        this: First handler.
        other: Second handler.

    Returns:
        True if both handlers are equivalent.
    """
    if type(this) is not type(other):
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
    """Enable stdout logging for a logger if not already configured.

    Args:
        logger: Logger instance or name.
        format: Format string or existing Formatter instance.
        level: Logging level for the handler.

    Returns:
        The configured ``logging.Logger`` instance.
    """
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)

    handler = get_stdout_handler(format=format, level=level)

    if any([check_handler_equality(handler, existing) for existing in get_all_handlers(logger)]):
        return logger

    logger.addHandler(handler)
    return logger


class LoggingMixin:
    """Mixin that provides a cached logger instance based on the class name."""

    @cached_property
    def logger(self) -> logging.Logger:
        """A logger named after the module and class."""
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(name)

    @property
    def log(self) -> logging.Logger:
        """Alias for ``logger``."""
        return self.logger

    def log_stacktrace(self, message: str, error: BaseException):
        """Log an error message and its stack trace.

        Args:
            message: Error message to log.
            error: The exception to log.
        """
        self.logger.error(message)
        self.logger.exception(error)

    def enable_stdout_logging(self):
        """Enable stdout logging for this instance's logger."""
        enable_stdout_logging(self.logger)
