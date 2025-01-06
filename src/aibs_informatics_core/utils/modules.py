__all__ = [
    "as_module_type",
    "get_all_subclasses",
    "load_all_modules_from_pkg",
]

import importlib
import inspect
import logging
import pkgutil
from types import ModuleType
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union, overload

logger = logging.getLogger(__name__)

T = TypeVar("T")


def as_module_type(package: Union[str, ModuleType]) -> ModuleType:
    return package if isinstance(package, ModuleType) else importlib.import_module(package)


@overload
def load_type_from_qualified_name(qualified_name: str, expected_type: Type[T]) -> T:
    ...


@overload
def load_type_from_qualified_name(qualified_name: str, expected_type: Literal[None] = None) -> Any:
    ...


def load_type_from_qualified_name(
    qualified_name: str, expected_type: Optional[Type[T]] = None
) -> Union[Any, T]:
    """Load a type from its fully qualified name

    Args:
        qualified_name (str): fully qualified name of type

    Returns:
        (type): type object
    """
    if "." not in qualified_name:
        module_name = "builtins"
        type_name = qualified_name
    else:
        module_name, type_name = qualified_name.rsplit(".", 1)
    module = as_module_type(module_name)
    if not hasattr(module, type_name):
        raise ValueError(f"Unable to find type {type_name} in module {module_name}")
    loaded_type = getattr(module, type_name)
    if expected_type is not None and not issubclass(loaded_type, expected_type):
        raise ValueError(
            f"Loaded type {loaded_type} is not a subclass of expected type {expected_type}"
        )
    return loaded_type


def get_all_subclasses(cls: Type[T], ignore_abstract: bool = False) -> List[Type[T]]:
    """Get all loaded subclasses of a given class

    Args:
        cls: class object
        ignore_abstract (bool): boolean to filter out abstract classes

    Returns:
        (list): all subclasses imported into python

    """
    subclasses = cls.__subclasses__() + [
        g for sub_cls in cls.__subclasses__() for g in get_all_subclasses(sub_cls)
    ]
    return [
        subclass
        for subclass in subclasses
        if not ignore_abstract or not inspect.isabstract(subclass)
    ]


def load_all_modules_from_pkg(
    package: Union[str, ModuleType],
    recursive: bool = True,
    include_packages: bool = False,
) -> Dict:
    """
    Import all modules found within the package

    Args:
        package (string_types, module): imported module or string name of module
        recursive (bool): whether to recursively import modules.
        include_packages (bool): whether to include packages in results
    Returns:
        (dict): mapping of package/module to module
    """
    mod_type_package: ModuleType = as_module_type(package)
    # If package is actually a module, then return as is.
    if not hasattr(mod_type_package, "__path__"):
        return {mod_type_package.__package__: mod_type_package}
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(mod_type_package.__path__):  # type: ignore  # mypy issue #1422
        full_name = mod_type_package.__name__ + "." + name
        if include_packages or not is_pkg:
            results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(
                load_all_modules_from_pkg(
                    full_name, recursive=recursive, include_packages=include_packages
                )
            )
    return results


def get_qualified_name(obj: Any) -> str:
    """Returns the fully qualified name of the object provided.

    Resources:
    - PEP 3155 for qualified name https://peps.python.org/pep-3155/
    - solution from https://stackoverflow.com/questions/2020014/get-fully-qualified-class-name-of-an-object-in-python

    Args:
        obj (Any): variable to get qualified name of (class, function, object etc.)

    Returns:
        str: fully qualified name of object
    """
    try:
        # if obj is a class or function, get module directly
        module = obj.__module__
    except AttributeError:
        # then get module from o's class
        module = obj.__class__.__module__
    try:
        # if o is a class or function, get name directly
        name = obj.__qualname__
    except AttributeError:
        # then get o's class name
        name = obj.__class__.__qualname__ if not isinstance(obj, ModuleType) else obj.__name__
    # if o is a method of builtin class, then module will be None
    if module == "builtins" or module is None:
        return name
    return module + "." + name
