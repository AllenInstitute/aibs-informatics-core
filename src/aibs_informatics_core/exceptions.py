# --------------------------------------------------------------------------
# Generic Exceptions
# --------------------------------------------------------------------------
class ApplicationException(Exception):
    """Generic Exception for Application Errors"""


class ValidationError(ApplicationException, ValueError):
    """Generic validation error class"""
