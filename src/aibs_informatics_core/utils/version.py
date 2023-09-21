__all__ = [
    "get_version",
]

from importlib.metadata import version


def get_version(distribution_name: str) -> str:
    return version(distribution_name=distribution_name)
