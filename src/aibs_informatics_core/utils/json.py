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
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def is_json_str(data: Any) -> bool:
    try:
        assert isinstance(data, str)
        json.loads(data)
    except Exception:
        return False
    return True


def load_json(path_or_str: str | Path, **kwargs) -> JSON:
    if isinstance(path_or_str, str) and is_json_str(path_or_str):
        return json.loads(path_or_str, **kwargs)
    elif Path(path_or_str).exists():
        with open(str(path_or_str)) as f:
            return json.load(f, **kwargs)
    else:
        raise ValueError(f"Cannot load {path_or_str} as json. Not valid json string or path.")


def load_json_object(path_or_str: str | Path, **kwargs) -> dict[str, JSON]:
    json_data = load_json(path_or_str, **kwargs)
    if not isinstance(json_data, dict):
        raise ValueError(f"{path_or_str} was loaded as JSON but not a JSON Object")
    return cast(dict[str, JSON], json_data)
