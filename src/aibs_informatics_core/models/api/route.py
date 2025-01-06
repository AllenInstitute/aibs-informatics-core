# needed for python 3.11 to enable postponed evaluation of annotations
from __future__ import annotations

import aibs_informatics_core

__all__ = [
    "ApiRoute",
    "ApiClientInterface",
    "ApiRequestConfig",
    "ClientRouteMethod",
    "BoundClientRouteMethod",
]

import logging
import re
import sys
from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Match,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import requests  # type: ignore[import-untyped]
from requests.auth import AuthBase  # type: ignore[import-untyped]

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.api.http_parameters import HTTPParameters
from aibs_informatics_core.models.base import (
    CustomStringField,
    ModelProtocol,
    SchemaModel,
    custom_field,
)
from aibs_informatics_core.models.version import VersionStr
from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.os_operations import get_env_var
from aibs_informatics_core.utils.tools.strtools import removesuffix
from aibs_informatics_core.utils.version import get_version

if sys.version_info >= (3, 10):
    from inspect import get_annotations
else:  # pragma: no cover
    import types
    from typing import Callable, Mapping, Optional, Union

    # not supported in 3.9
    def get_annotations(
        obj: Union[Callable[..., object], Type[Any], types.ModuleType],
        *,
        globals: Optional[Mapping[str, Any]] = None,
        locals: Optional[Mapping[str, Any]] = None,
        eval_str: bool = False,
    ) -> Dict[str, Any]:
        return obj.__annotations__


T = TypeVar("T")
AuthType = TypeVar("AuthType", bound=AuthBase)

logger = logging.getLogger(__name__)


API_SERVICE_LOG_LEVEL_ENV_VAR = "API_LOG_LEVEL"
API_SERVICE_LOG_LEVEL_KEY = "x-log-level"

CLIENT_VERSION_ENV_VAR = "API_CLIENT_VERSION"
CLIENT_VERSION_KEY = "x-client-version"

CLIENT_VERSION_PACKAGE_ENV_VAR = "API_CLIENT_VERSION_PACKAGE"

DYNAMIC_ROUTE_PATTERN = re.compile(r"(<(\w+)>)")


API_REQUEST = TypeVar("API_REQUEST", bound=ModelProtocol)
API_RESPONSE = TypeVar("API_RESPONSE", bound=ModelProtocol)


@dataclass
class ApiRequestConfig(SchemaModel):
    client_version: VersionStr = custom_field(mm_field=CustomStringField(VersionStr))
    service_log_level: Optional[str] = custom_field(default=None)

    client_version_default: ClassVar[Optional[VersionStr]] = None
    client_version_package_name_default: ClassVar[str] = aibs_informatics_core.__name__

    def to_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            CLIENT_VERSION_KEY: str(self.client_version),
        }
        if self.service_log_level:
            headers[API_SERVICE_LOG_LEVEL_KEY] = self.service_log_level

        return headers

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> ApiRequestConfig:
        return cls.from_dict(
            dict(
                client_version=headers.get(CLIENT_VERSION_KEY),
                service_log_level=headers.get(API_SERVICE_LOG_LEVEL_KEY),
            )
        )

    @classmethod
    def build(cls, **kwargs) -> ApiRequestConfig:
        client_version = cls.build__client_version(**kwargs)
        service_log_level = get_env_var(API_SERVICE_LOG_LEVEL_ENV_VAR)

        return cls(
            client_version=client_version,
            service_log_level=service_log_level,
        )

    @classmethod
    def build__client_version(cls, **kwargs) -> VersionStr:
        """Builds the client version

        Order of precedence:
        1. "client_version" in kwargs
        2. "client_version_package_name" in kwargs -> get_version(VALUE)
        3. client_version_default (if set) in class
        4. client_version_package_name_default in class -> get_version(VALUE)

        Returns:
            VersionStr: version string resolved from the above order of precedence
        """
        if "client_version" in kwargs:
            return VersionStr(kwargs["client_version"])
        elif "client_version_package_name" in kwargs:
            return VersionStr(get_version(kwargs["client_version_package_name"]))
        elif cls.client_version_default:
            return cls.client_version_default
        elif cls.client_version_package_name_default:
            return VersionStr(get_version(cls.client_version_package_name_default))
        else:  # pragma: no cover
            raise ValueError("Could not resolve client version")


class ApiHeadersMixin:
    request_config_cls: ClassVar[Type[ApiRequestConfig]] = ApiRequestConfig

    @classmethod
    def generate_headers(cls) -> Dict[str, str]:
        """Custom headers attached with each client request

        Returns:
            Dict[str, Any]: dictionary of header key-value pairs
        """
        return cls.request_config_cls.build().to_headers()

    @classmethod
    def validate_headers(
        cls,
        headers: Dict[str, str],
        minimum_client_version: Optional[Union[VersionStr, str]] = None,
    ) -> None:
        config = cls.resolve_request_config(headers)

        # validate client version
        if minimum_client_version:
            minimum_client_version = VersionStr(minimum_client_version)
            if config.client_version < minimum_client_version:
                raise ValueError(
                    f"Client version {config.client_version} is too old. "
                    f"Must use client version {minimum_client_version} or newer"
                )

    @classmethod
    def resolve_request_config(cls, headers: Dict[str, str]) -> ApiRequestConfig:
        return cls.request_config_cls.from_headers(headers)


class ApiRoute(Generic[API_REQUEST, API_RESPONSE], ApiHeadersMixin):
    @classmethod
    @abstractmethod
    def route_rule(cls) -> str:
        """The rule for the given API route

        Returns:
            str: a rule (e.g. /prefix/route/<execution_id>)
        """
        raise NotImplementedError("Specify a rule for the given API route")  # pragma: no cover

    @classmethod
    @abstractmethod
    def route_method(cls) -> Union[str, List[str]]:
        """Specifies the methods available

        Returns:
            Union[str, List[str]]: e.g. ['POST', 'PUT'], 'GET'
        """
        raise NotImplementedError("Specify a method for the given API route")  # pragma: no cover

    @classmethod
    def primary_route_method(cls) -> str:
        method = cls.route_method()
        return next(iter(method)) if isinstance(method, list) else method

    @classmethod
    def route_rule_param_keys(cls) -> List[str]:
        return [key for (_, key) in DYNAMIC_ROUTE_PATTERN.findall(cls.route_rule())]

    @classmethod
    def service_name(cls) -> str:
        return cls.__name__

    @classmethod
    def get_request_cls(cls) -> Type[API_REQUEST]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    @classmethod
    def get_response_cls(cls) -> Type[API_RESPONSE]:
        return cls.__orig_bases__[0].__args__[1]  # type: ignore

    @classmethod
    def get_client_method_name(cls) -> str:
        client_method_name = re.sub(
            "((?<=[a-z])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", cls.__name__
        ).lower()
        return removesuffix(client_method_name, "_route")

    @classmethod
    def get_http_request(
        cls, request: API_REQUEST, base_url: str, **request_kwargs
    ) -> requests.Request:
        """

        Args:
            request (API_REQUEST): _description_
            base_url (str): _description_

        Returns:
            requests.Request: _description_
        """

        http_parameters = cls.get_http_parameters_from_request(request)

        route_path = cls._get_route_path(http_parameters)
        url = f"{base_url}{route_path}"

        if "headers" not in request_kwargs:
            request_kwargs["headers"] = cls.generate_headers()

        http_request = requests.Request(
            method=cls.primary_route_method(),
            url=url,
            json=http_parameters.stringified_request_body,
            params=http_parameters.stringified_query_params,
            **request_kwargs,
        )
        return http_request

    @classmethod
    def get_request_from_http_parameters(cls, http_parameters: HTTPParameters) -> API_REQUEST:
        request_cls = cls.get_request_cls()
        return request_cls.from_dict(http_parameters.merged_params)

    @classmethod
    def get_http_parameters_from_request(cls, request: API_REQUEST) -> HTTPParameters:
        request_body = cast(Dict[str, JSON], request.to_dict())

        # Initialize the two parameter types
        route_params = {}
        query_params = {}

        for route_param_key in cls.route_rule_param_keys():
            if route_param_key not in request_body:
                raise ValidationError(
                    f"{route_param_key} specified in {cls.route_rule()} is not a valid field"
                    f"in the request class {request.__class__}"
                )
            route_params[route_param_key] = request_body.pop(route_param_key)

        method = cls.primary_route_method()
        if method == "GET":
            query_params = request_body.copy()
            request_body = {}
        return HTTPParameters(
            route_params=route_params,
            query_params=query_params,
            request_body=request_body,
        )

    @classmethod
    def _get_route_path(cls, http_parameters: HTTPParameters) -> str:
        str_route_parameters = http_parameters.stringified_route_params

        def _stringify_field(dynamic_route_match: Match) -> str:
            field_name = dynamic_route_match.group(2)
            try:
                return str_route_parameters[field_name]
            except Exception as e:
                raise ValidationError(
                    f"Couldn't resolve {field_name} from {str_route_parameters}"
                ) from e

        return DYNAMIC_ROUTE_PATTERN.sub(repl=_stringify_field, string=cls.route_rule())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(rule={self.route_rule()}, method={self.route_method()})"

    @classmethod
    def create_route_method(cls) -> ClientRouteMethod[API_REQUEST, API_RESPONSE]:
        def route_method(self: ApiClientInterface, request: API_REQUEST) -> API_RESPONSE:
            return self.call(cls(), request)

        return cast(ClientRouteMethod[API_REQUEST, API_RESPONSE], route_method)


class ApiClientInterface(Protocol):
    def call(
        self, route: ApiRoute[API_REQUEST, API_RESPONSE], request: API_REQUEST
    ) -> API_RESPONSE:
        ...  # pragma: no cover


# Solution for adding class methods to client class with named arguments
# https://github.com/python/typing/discussions/1040
class BoundClientRouteMethod(Protocol, Generic[API_REQUEST, API_RESPONSE]):  # type: ignore
    def __call__(self, request: API_REQUEST) -> API_RESPONSE:
        ...  # pragma: no cover


class ClientRouteMethod(Protocol, Generic[API_REQUEST, API_RESPONSE]):  # type: ignore
    def __call__(__self, self: ApiClientInterface, request: API_REQUEST) -> API_RESPONSE:
        ...  # pragma: no cover

    @overload
    def __get__(
        self, obj: ApiClientInterface, objtype: Optional[Type[ApiClientInterface]] = None
    ) -> BoundClientRouteMethod[API_REQUEST, API_RESPONSE]:
        ...  # pragma: no cover

    @overload
    def __get__(  # type: ignore[misc]
        self, obj: None, objtype: Optional[Type[ApiClientInterface]] = None
    ) -> ClientRouteMethod[API_REQUEST, API_RESPONSE]:
        ...  # pragma: no cover

    def __get__(
        self,
        obj: Optional[ApiClientInterface],
        objtype: Optional[Type[ApiClientInterface]] = None,
    ) -> Union[
        BoundClientRouteMethod[API_REQUEST, API_RESPONSE],
        ClientRouteMethod[API_REQUEST, API_RESPONSE],
    ]:
        ...  # pragma: no cover
