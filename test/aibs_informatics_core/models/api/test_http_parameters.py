import json
from dataclasses import dataclass
from test.base import BaseTest
from typing import Any, Dict, List, Optional

import requests
from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.api.http_parameters import QUERY_PARAMS_KEY, HTTPParameters
from aibs_informatics_core.models.api.route import (
    API_SERVICE_LOG_LEVEL_ENV_VAR,
    API_SERVICE_LOG_LEVEL_KEY,
    CLIENT_VERSION_KEY,
    ApiRequestConfig,
    ApiRoute,
)
from aibs_informatics_core.models.base.model import ModelProtocol, SchemaModel
from aibs_informatics_core.models.version import VersionStr

from .helpers import (
    BaseRequest,
    BaseResponse,
    DynamicGetterResourceRoute,
    DynamicPostResourceRoute,
    GetterResourceRoute,
    PostResourceRoute,
)

test_cases = [
    param(
        GetterResourceRoute(),
        BaseRequest(id_str="imanid"),
        HTTPParameters({}, {"id_str": "imanid"}, {}),
        id="GET Route with only required fields converted",
    ),
    param(
        DynamicGetterResourceRoute(),
        BaseRequest(id_str="imanid"),
        HTTPParameters({"id_str": "imanid"}, {}, {}),
        id="Dynamic GET Route with only required fields converted",
    ),
    param(
        PostResourceRoute(),
        BaseRequest(id_str="imanid"),
        HTTPParameters({}, {}, {"id_str": "imanid"}),
        id="POST Route with only required fields converted",
    ),
    param(
        DynamicPostResourceRoute(),
        BaseRequest(id_str="imanid"),
        HTTPParameters({"id_str": "imanid"}, {}, {}),
        id="Dynamic POST Route with only required fields converted",
    ),
    param(
        GetterResourceRoute(),
        BaseRequest(id_str="imanid", any_list=["a", 1], any_map={"strkey": "strvalue", "1": 1}),
        HTTPParameters(
            {},
            {
                "id_str": "imanid",
                "any_list": ["a", 1],
                "any_map": {"strkey": "strvalue", "1": 1},
            },
            {},
        ),
        id="GET Route with list and dict fields converted",
    ),
    param(
        DynamicGetterResourceRoute(),
        BaseRequest(id_str="imanid", any_list=["a", 1], any_map={"strkey": "strvalue", "1": 1}),
        HTTPParameters(
            {
                "id_str": "imanid",
            },
            {
                "any_list": ["a", 1],
                "any_map": {"strkey": "strvalue", "1": 1},
            },
            {},
        ),
        id="Dynamic GET Route with list and dict fields converted",
    ),
    param(
        PostResourceRoute(),
        BaseRequest(id_str="imanid", any_list=["a", 1], any_map={"strkey": "strvalue", "1": 1}),
        HTTPParameters(
            {},
            {},
            {
                "id_str": "imanid",
                "any_list": ["a", 1],
                "any_map": {"strkey": "strvalue", "1": 1},
            },
        ),
        id="POST Route with list and dict fields converted",
    ),
    param(
        DynamicPostResourceRoute(),
        BaseRequest(id_str="imanid", any_list=["a", 1], any_map={"strkey": "strvalue", "1": 1}),
        HTTPParameters(
            {
                "id_str": "imanid",
            },
            {},
            {
                "any_list": ["a", 1],
                "any_map": {"strkey": "strvalue", "1": 1},
            },
        ),
        id="Dynamic POST Route with list and dict fields converted",
    ),
]


@mark.parametrize("route,request_model,expected", test_cases)
def test__get_http_parameters_from_request__works(
    route: ApiRoute, request_model: ModelProtocol, expected: HTTPParameters
):
    actual = route.get_http_parameters_from_request(request_model)
    assert expected == actual


@mark.parametrize("route,expected,params", test_cases)
def test__get_request_from_http_parameters__works(
    route: ApiRoute, params: HTTPParameters, expected: ModelProtocol
):
    actual = route.get_request_from_http_parameters(params)
    assert expected == actual


def test__from_stringified_route_params__handles_bad():
    stringified = {"x": "X(x)"}
    actual = HTTPParameters.from_stringified_route_params(stringified)
    assert actual == stringified


def test__to_stringified_route_params__fails():
    class X:
        def __str__(self) -> str:
            raise ValueError("I am a bad object")

    with raises(ValidationError):
        HTTPParameters.to_stringified_route_params({"x": X()})


def test__to_and_from_stringified_route_params__works():
    original = {"any_dict": {"a": "b", "c": [1, 2, 3]}, "any_list": ["a", 1], "any_int": 1}
    expected_stringified = {
        "any_dict": "{'a': 'b', 'c': [1, 2, 3]}",
        "any_list": "['a', 1]",
        "any_int": "1",
    }

    actual_stringified = HTTPParameters.to_stringified_route_params(original)
    actual = HTTPParameters.from_stringified_route_params(actual_stringified)

    assert actual_stringified == expected_stringified
    assert actual == original


def test__from_stringified_query_params__handles_empty():
    assert HTTPParameters.from_stringified_query_params({}) == {}
    assert HTTPParameters.from_stringified_query_params(None) == {}


def test__from_stringified_query_params__fails_if_key_missing():
    with raises(ValidationError):
        HTTPParameters.from_stringified_query_params({"notdata": "x"})


def test__to_and_from_stringified_query_params__handles_empty():
    original = {"any_dict": {"a": "b", "c": [1, 2, 3]}, "any_list": ["a", 1], "any_int": 1}

    stringified = HTTPParameters.to_stringified_query_params(original)
    reconstructed = HTTPParameters.from_stringified_query_params(stringified)

    assert QUERY_PARAMS_KEY in stringified
    assert reconstructed == original


def test__from_stringified_request_body__handles_empty():
    assert HTTPParameters.from_stringified_request_body(None) == {}
    assert HTTPParameters.from_stringified_request_body("") == {}


def test__to_and_from_stringified_request_body__handles_empty():
    original = {"any_dict": {"a": "b", "c": [1, 2, 3]}, "any_list": ["a", 1], "any_int": 1}

    stringified = HTTPParameters.to_stringified_request_body(original)
    reconstructed = HTTPParameters.from_stringified_request_body(stringified)

    assert reconstructed == original


def test__from_http_request__handles_empties():
    assert HTTPParameters.from_http_request({}, {}, None) == HTTPParameters({}, {}, {})
