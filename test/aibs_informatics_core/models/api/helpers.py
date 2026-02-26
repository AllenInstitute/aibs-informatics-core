from dataclasses import dataclass
from typing import Any

from aibs_informatics_core.models.api.route import ApiRoute
from aibs_informatics_core.models.base.model import SchemaModel


@dataclass
class BaseRequest(SchemaModel):
    id_str: str
    any_str: str | None = None
    any_int: int | None = None
    any_bool: bool | None = None
    any_list: list[Any] | None = None
    any_map: dict[Any, Any] | None = None


@dataclass
class BaseResponse(SchemaModel):
    any_str: str | None = None


class GetterResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return "/test/resource"

    @classmethod
    def route_method(cls) -> str:
        return "GET"


class DynamicGetterResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return "/test/<id_str>/resource"

    @classmethod
    def route_method(cls) -> str:
        return "GET"


class PostResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return "/test/resource"

    @classmethod
    def route_method(cls) -> str:
        return "POST"


class DynamicPostResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return "/test/<id_str>/resource"

    @classmethod
    def route_method(cls) -> str:
        return "POST"
