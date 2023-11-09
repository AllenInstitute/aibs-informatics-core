__all__ = [
    "remove_null_values",
    "remove_matching_values",
    "flatten_dict",
    "nested_dict",
    "convert_key_case",
]


from copy import deepcopy
from typing import Any, Callable, Dict, List, MutableMapping, Tuple, TypeVar, cast

T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


def remove_null_values(
    orig_dict: MutableMapping[KT, VT],
    in_place: bool = False,
    recursive: bool = False,
) -> MutableMapping[KT, VT]:
    """Removes null values from a dictionary object

    Args:
        orig_dict (MutableMapping[KT, VT]): target dictionary to prune null values from
        in_place (bool, optional): whether to do operation on target in place. Defaults to False.
        recursive (bool, optional): whether to prune recursively. Defaults to False.

    Returns:
        MutableMapping[KT, VT]: pruned dictionary
    """
    return remove_matching_values(
        orig_dict=orig_dict, in_place=in_place, recursive=recursive, target_value=None
    )


def remove_matching_values(
    orig_dict: MutableMapping[KT, VT],
    in_place: bool = False,
    recursive: bool = False,
    target_value: Any = None,
) -> MutableMapping[KT, VT]:
    """Filter out keys with values matching target value

    Args:
        orig_dict (MutableMapping[KT, VT]): Original dictionary
        in_place (bool, optional): If true, removes keys in place. Defaults to False.
        recursive (bool, optional): If true, recursively removes values if target value.
            Defaults to False.

    Returns:
        MutableMapping[KT, VT]: dictionary without target values
    """
    filtered_dict = orig_dict if in_place else deepcopy(orig_dict)

    for k, v in list(filtered_dict.items()):
        if isinstance(v, dict) and recursive:
            filtered_dict[k] = cast(VT, remove_null_values(v, in_place=True, recursive=recursive))
        elif v == target_value:
            filtered_dict.pop(k)
    return filtered_dict


def flatten_dict(
    data: MutableMapping[str, Any], parent_key: str = "", delimiter: str = "."
) -> Dict[str, Any]:
    """
    Flattens a nested dictionary by concatenating the keys with a given delimiter.

    Args:
    data (Dict[str, Any]): The dictionary to flatten.
    parent_key (str, optional): The concatenated key for the nested items. Defaults to ''.
    delimiter (str, optional): The delimiter to use for concatenating the keys. Defaults to '.'.

    Returns:
    Dict[str, Any]: The flattened dictionary.
    """
    items: List[Tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{delimiter}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, delimiter).items())
        else:
            items.append((new_key, value))
    return dict(items)


def nested_dict(data: MutableMapping[str, Any], delimiter: str = ".") -> Dict[str, Any]:
    """
    Creates a nested dictionary by splitting the keys by a given delimiter.

    Args:
    data (Dict[str, Any]): The dictionary to transform.
    delimiter (str, optional): The delimiter to use for splitting the keys. Defaults to '.'.

    Returns:
    Dict[str, Any]: The transformed, nested dictionary.

    Raises:
    ValueError: If a collision is detected during the transformation process.
    """
    result: Dict[str, Any] = {}
    for key, value in data.items():
        parts = key.split(delimiter)
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            elif not isinstance(d[part], dict):
                raise ValueError(f"Key collision detected at '{part}' when processing '{key}'")
            d = d[part]
        if parts[-1] in d and d[parts[-1]] != value:
            raise ValueError(f"Key collision detected at '{parts[-1]}' when processing '{key}'")
        d[parts[-1]] = value
    return result


def convert_key_case(data: T, key_case: Callable[[str], str]) -> T:
    if isinstance(data, dict):
        return {
            (key_case(k) if isinstance(k, str) else k): convert_key_case(v, key_case)
            for k, v in data.items()
        }  # type: ignore
    elif isinstance(data, list):
        return [convert_key_case(item, key_case) for item in data]  # type: ignore
    else:
        return data
