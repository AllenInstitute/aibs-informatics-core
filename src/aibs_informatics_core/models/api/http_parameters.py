__all__ = ["HTTPParameters"]


import ast
import json
import urllib.parse
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.logging import get_logger

logger = get_logger()


QUERY_PARAMS_KEY = "data"


@dataclass
class HTTPParameters:
    route_params: dict[str, JSON] | None
    query_params: dict[str, JSON] | None
    request_body: dict[str, JSON] | None

    @property
    def stringified_route_params(self) -> dict[str, str]:
        return self.to_stringified_route_params(self.route_params)

    @property
    def stringified_query_params(self) -> dict[str, str]:
        return self.to_stringified_query_params(self.query_params)

    @property
    def stringified_request_body(self) -> str | None:
        return self.to_stringified_request_body(self.request_body)

    @property
    def merged_params(self) -> dict[str, JSON]:
        request_json = {}
        # First add route parameters
        if self.route_params:
            request_json.update(self.route_params)
        # Next add query parameters
        if self.query_params:
            request_json.update(self.query_params)
        # finally add request body
        if self.request_body:
            request_json.update(self.request_body)
        return request_json

    @classmethod
    def from_stringified_route_params(cls, parameters: dict[str, str] | None) -> dict[str, JSON]:
        evaluated_params = dict()

        input_params = parameters or dict()
        # literal_eval as much as we can to python primitives, our schema will take care of rest.
        for k, v in input_params.items():
            try:
                evaluated_params[k] = ast.literal_eval(urllib.parse.unquote(v))
            except Exception:
                logger.warning(f"could not parse {v}. setting as is.")
                evaluated_params[k] = v
        return evaluated_params

    @classmethod
    def to_stringified_route_params(cls, parameters: dict[str, JSON] | None) -> dict[str, str]:
        string_params = {}
        for k, v in (parameters or {}).items():
            try:
                string_params[k] = str(v)
            except Exception as e:
                raise ValidationError(f"Couldn't stringify {k} value=?") from e
        return string_params

    @classmethod
    def from_stringified_query_params(cls, parameters: dict[str, str] | None) -> dict[str, JSON]:
        if parameters is None or len(parameters) == 0:
            return {}
        elif QUERY_PARAMS_KEY not in parameters:
            raise ValidationError(
                f"Stringified Query parameters MUST have {QUERY_PARAMS_KEY} field"
            )
        parameters_str = urlsafe_b64decode(parameters[QUERY_PARAMS_KEY].encode()).decode()
        return json.loads(parameters_str)

    @classmethod
    def to_stringified_query_params(cls, parameters: dict[str, JSON] | None) -> dict[str, str]:
        if parameters is None or len(parameters) == 0:
            return {}
        parameters_str = json.dumps(parameters, sort_keys=True)
        return {QUERY_PARAMS_KEY: urlsafe_b64encode(parameters_str.encode()).decode()}

    @classmethod
    def to_stringified_request_body(cls, parameters: dict[str, JSON] | None) -> str | None:
        if parameters is None or len(parameters) == 0:
            return None
        return json.dumps(parameters, sort_keys=True)

    @classmethod
    def from_stringified_request_body(cls, parameters: str | None) -> dict[str, JSON]:
        if parameters is None or len(parameters) == 0:
            return {}
        return json.loads(parameters)

    @classmethod
    def from_http_request(
        cls,
        stringified_route_params: dict[str, str] | None,
        stringified_query_params: dict[str, str] | None,
        stringified_request_body: str | None,
    ) -> "HTTPParameters":
        return HTTPParameters(
            route_params=cls.from_stringified_route_params(stringified_route_params),
            query_params=cls.from_stringified_query_params(stringified_query_params),
            request_body=cls.from_stringified_request_body(stringified_request_body),
        )
