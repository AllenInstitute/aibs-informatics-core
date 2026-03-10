__all__ = [
    "JSON",
    "DecimalEncoder",
    "is_json_str",
    "load_json",
    "load_json_object",
]

import decimal
import json
from pathlib import Path
from typing import Any, TypeAlias, cast

from pydantic import JsonValue

JSON: TypeAlias = JsonValue
JSONObject: TypeAlias = dict[str, JSON]
JSONArray: TypeAlias = list[JSON]


class DecimalEncoder(json.JSONEncoder):
    """Used to encode decimal.Decimal when printing/encoding dicts to
    JSON strings
    """

    def default(self, o: Any) -> str | json.JSONEncoder:
        """Encode ``decimal.Decimal`` values as strings.

        Args:
            o: The object to encode.

        Returns:
            String representation for Decimal values, otherwise delegates to parent.
        """
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def is_json_str(data: Any) -> bool:
    """Check if a value is a valid JSON string.

    Args:
        data: The value to check.

    Returns:
        True if ``data`` is a string containing valid JSON.
    """
    try:
        assert isinstance(data, str)
        json.loads(data)
    except Exception:
        return False
    return True


def load_json(path_or_str: str | Path, **kwargs) -> JSON:
    """Load JSON from a string or file path.

    Args:
        path_or_str: A JSON string or path to a JSON file.
        **kwargs: Additional keyword arguments passed to ``json.loads`` or ``json.load``.

    Returns:
        The parsed JSON value.

    Raises:
        ValueError: If the input is neither a valid JSON string nor an existing file path.
    """
    if isinstance(path_or_str, str) and is_json_str(path_or_str):
        return json.loads(path_or_str, **kwargs)
    elif Path(path_or_str).exists():
        with open(str(path_or_str)) as f:
            return json.load(f, **kwargs)
    else:
        raise ValueError(f"Cannot load {path_or_str} as json. Not valid json string or path.")


def load_json_object(path_or_str: str | Path, **kwargs) -> dict[str, JSON]:
    """Load a JSON object (dict) from a string or file path.

    Args:
        path_or_str: A JSON string or path to a JSON file.
        **kwargs: Additional keyword arguments passed to ``load_json``.

    Returns:
        The parsed JSON object as a dictionary.

    Raises:
        ValueError: If the loaded JSON is not a dictionary.
    """
    json_data = load_json(path_or_str, **kwargs)
    if not isinstance(json_data, dict):
        raise ValueError(f"{path_or_str} was loaded as JSON but not a JSON Object")
    return cast(dict[str, JSON], json_data)
