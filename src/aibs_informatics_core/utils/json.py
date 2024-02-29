from __future__ import annotations

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
from typing import TYPE_CHECKING, Any, Dict, List, Protocol, Type, TypeVar, Union, cast

# TODO: Figure out better JSON typing. mypy doesn't like
JSON = Union[Dict[str, Any], List[Any], int, str, float, bool, Type[None]]
# JSON = Union['JSONArray', 'JSONObject', int, str, float, bool, Type[None]]


if TYPE_CHECKING:  # pragma: no cover

    class JSONArray(list[JSON], Protocol):  # type: ignore
        # __class__: Type[list[JSON]]  # type: ignore[assignment]
        pass

    class JSONObject(dict[str, JSON], Protocol):  # type: ignore
        # __class__: Type[dict[str, JSON]]  # type: ignore[assignment]
        pass

else:
    JSONArray, JSONObject = List[Any], Dict[str, Any]


class DecimalEncoder(json.JSONEncoder):
    """Used to encode decimal.Decimal when printing/encoding dicts to
    JSON strings
    """

    def default(self, o: Any) -> Union[str, json.JSONEncoder]:
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def is_json_str(data: Any) -> bool:
    try:
        assert isinstance(data, str)
        json.loads(data)
    except:
        return False
    return True


def load_json(path_or_str: Union[str, Path], **kwargs) -> JSON:
    if isinstance(path_or_str, str) and is_json_str(path_or_str):
        return json.loads(path_or_str, **kwargs)
    elif Path(path_or_str).exists():
        with open(str(path_or_str), "r") as f:
            return json.load(f, **kwargs)
    else:
        raise ValueError(f"Cannot load {path_or_str} as json. Not valid json string or path.")


def load_json_object(path_or_str: Union[str, Path], **kwargs) -> JSONObject:
    json_data = load_json(path_or_str, **kwargs)
    if not isinstance(json_data, dict):
        raise ValueError(f"{path_or_str} was loaded as JSON but not a JSON Object")
    return cast(JSONObject, json_data)
