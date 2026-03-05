__all__ = [
    "JSONArray",
    "JSONObject",
    "JSON",
    "DecimalEncoder",
    "is_json_str",
    "load_json",
    "load_json_object",
]

import decimal
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, cast

JSON: TypeAlias = dict[str, Any] | list[Any] | int | str | float | bool | None


if TYPE_CHECKING:  # pragma: no cover

    class JSONArray(list[JSON], Protocol):  # type: ignore
        # __class__: type[list[JSON]]
        pass

    class JSONObject(dict[str, JSON], Protocol):  # type: ignore
        # __class__: Type[dict[str, JSON]]
        pass
else:
    JSONArray, JSONObject = list[Any], dict[str, Any]


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


def load_json_object(path_or_str: str | Path, **kwargs) -> JSONObject:
    json_data = load_json(path_or_str, **kwargs)
    if not isinstance(json_data, dict):
        raise ValueError(f"{path_or_str} was loaded as JSON but not a JSON Object")
    return cast(JSONObject, json_data)
