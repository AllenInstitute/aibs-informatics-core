# --------------------------------------------------------------------------
# Generic Exceptions
# --------------------------------------------------------------------------
class ApplicationException(Exception):
    """Generic Exception for Application Errors"""


class ValidationError(ValueError):
    """Generic validation error class"""
