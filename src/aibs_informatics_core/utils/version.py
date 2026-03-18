__all__ = [
    "get_version",
]

from importlib.metadata import version


def get_version(distribution_name: str) -> str:
    """Get the installed version of a Python distribution.

    Args:
        distribution_name: Name of the distribution package.

    Returns:
        The version string.
    """
    return version(distribution_name=distribution_name)
