from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aibs_informatics_core.models.api.route import ApiRoute
from aibs_informatics_core.models.base.model import SchemaModel


@dataclass
class BaseRequest(SchemaModel):
    id_str: str
    any_str: Optional[str] = None
    any_int: Optional[int] = None
    any_bool: Optional[bool] = None
    any_list: Optional[List[Any]] = None
    any_map: Optional[Dict[Any, Any]] = None


@dataclass
class BaseResponse(SchemaModel):
    any_str: Optional[str] = None


class GetterResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return f"/test/resource"

    @classmethod
    def route_method(cls) -> str:
        return "GET"


class DynamicGetterResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return f"/test/<id_str>/resource"

    @classmethod
    def route_method(cls) -> str:
        return "GET"


class PostResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return f"/test/resource"

    @classmethod
    def route_method(cls) -> str:
        return "POST"


class DynamicPostResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
    @classmethod
    def route_rule(cls) -> str:
        return f"/test/<id_str>/resource"

    @classmethod
    def route_method(cls) -> str:
        return "POST"
