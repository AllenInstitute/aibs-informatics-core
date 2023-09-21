import unittest

from aibs_informatics_core.utils.logging import LoggingMixin


class DummyClass(LoggingMixin):
    pass


class LoggingMixinTests(unittest.TestCase):
    def test__logger__provides_a_logger(self):
        dummy_class = DummyClass()
        logger1 = dummy_class.logger.info("info")
        logger1 = dummy_class.logger.warning("info")
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
