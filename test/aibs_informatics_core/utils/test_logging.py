import logging
import unittest

from aibs_informatics_core.utils.logging import (
    LoggingMixin,
    check_formatter_equality,
    check_handler_equality,
    enable_stdout_logging,
)


def test__check_handler_equality__works():
    handler1 = logging.StreamHandler()
    handler1.setLevel(logging.INFO)
    handler1.addFilter(logging.Filter())
    handler2 = logging.StreamHandler()
    handler2.setLevel(logging.INFO)
    handler2.addFilter(logging.Filter())
    assert check_handler_equality(handler1, handler2)
    handler2.set_name("different_name")
    assert not check_handler_equality(handler1, handler2)
    handler2.setLevel(logging.DEBUG)
    assert not check_handler_equality(handler1, handler2)
    assert not check_handler_equality(handler1, None)


def test__check_formatter_equality__works():
    fmt1 = logging.Formatter()
    fmt2 = logging.Formatter()
    assert check_formatter_equality(None, None)
    assert check_formatter_equality(fmt1, fmt2)
    assert not check_formatter_equality(fmt1, None)


def test__enable_stdout_logging__works():
    logger1 = enable_stdout_logging("test", level="INFO")
    logger2 = enable_stdout_logging("test", level="DEBUG")
    logger3 = enable_stdout_logging("test", format="%(message)s", level="INFO")
    assert len(logger1.handlers) == 3


class DummyClass(LoggingMixin):
    pass


class LoggingMixinTests(unittest.TestCase):
    def test__logger__provides_a_logger(self):
        dummy_class = DummyClass()
        logger1 = dummy_class.log.info("info")
        logger1 = dummy_class.log.warning("info")
        logger1 = dummy_class.logger.error("info")

    def test__log_stacktrace__works(self):
        dummy_class = DummyClass()

        try:
            raise ValueError("blah blah")
        except Exception as e:
            dummy_class.log_stacktrace("message", e)

    def test__logger__enable_stdout_logging(self):
        dummy_class = DummyClass()
        dummy_class.enable_stdout_logging()
