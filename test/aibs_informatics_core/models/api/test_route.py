import json
from test.base import BaseTest
from unittest import mock

import requests
from pytest import mark, param

from aibs_informatics_core.models.api.http_parameters import HTTPParameters
from aibs_informatics_core.models.api.route import (
    API_SERVICE_LOG_LEVEL_ENV_VAR,
    API_SERVICE_LOG_LEVEL_KEY,
    CLIENT_VERSION_KEY,
    ApiRequestConfig,
    ApiRoute,
)
from aibs_informatics_core.models.base.model import ModelProtocol
from aibs_informatics_core.models.version import VersionStr
from aibs_informatics_core.utils.version import get_version

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


def test__get_request_cls__returns_correct_class():
    assert GetterResourceRoute.get_request_cls() == BaseRequest


def test__get_response_cls__returns_correct_class():
    assert GetterResourceRoute.get_response_cls() == BaseResponse


DEFAULT_BASE_URL = "https://fake-api.com"


@mark.parametrize(
    "route,input,expected",
    [
        param(
            GetterResourceRoute(),
            BaseRequest(id_str="imanid"),
            requests.Request(
                method="GET",
                url=f"{DEFAULT_BASE_URL}/test/resource",
                params={"data": "eyJpZF9zdHIiOiAiaW1hbmlkIn0="},
                json=None,
            ),
            id="GET Route with only required fields",
        ),
        param(
            GetterResourceRoute(),
            BaseRequest(
                id_str="imanid",
                any_list=["a", 1],
                any_map={"strkey": "strvalue", "1": 1},
            ),
            requests.Request(
                method="GET",
                url=f"{DEFAULT_BASE_URL}/test/resource",
                params={
                    "data": "eyJhbnlfbGlzdCI6IFsiYSIsIDFdLCAiYW55X21hcCI6IHsiMSI6IDEsICJzdHJrZXkiOiAic3RydmFsdWUifSwgImlkX3N0ciI6ICJpbWFuaWQifQ=="  # noqa: E501
                },
            ),
            id="GET Route with list and dict fields converted",
        ),
        param(
            DynamicGetterResourceRoute(),
            BaseRequest(
                id_str="imanid",
                any_list=["a", 1],
                any_map={"strkey": "strvalue", "1": 1},
            ),
            requests.Request(
                method="GET",
                url=f"{DEFAULT_BASE_URL}/test/imanid/resource",
                params={
                    "data": "eyJhbnlfbGlzdCI6IFsiYSIsIDFdLCAiYW55X21hcCI6IHsiMSI6IDEsICJzdHJrZXkiOiAic3RydmFsdWUifX0="  # noqa: E501
                },
            ),
            id="(Dynamic) GET Route with list and dict fields converted",
        ),
        param(
            PostResourceRoute(),
            BaseRequest(
                id_str="imanid",
                any_list=["a", 1],
                any_map={"strkey": "strvalue", "1": 1},
            ),
            requests.Request(
                method="POST",
                url=f"{DEFAULT_BASE_URL}/test/resource",
                json=json.dumps(
                    BaseRequest(
                        id_str="imanid",
                        any_list=["a", 1],
                        any_map={"strkey": "strvalue", "1": 1},
                    ).to_dict(),
                    sort_keys=True,
                ),
            ),
            id="POST Route with list and dict fields converted",
        ),
        param(
            DynamicPostResourceRoute(),
            BaseRequest(
                id_str="imanid",
                any_list=["a", 1],
                any_map={"strkey": "strvalue", "1": 1},
            ),
            requests.Request(
                method="POST",
                url=f"{DEFAULT_BASE_URL}/test/imanid/resource",
                json='{"any_list": ["a", 1], "any_map": {"1": 1, "strkey": "strvalue"}}',
            ),
            id="(Dynamic) POST Route with list and dict fields converted",
        ),
    ],
)
def test__get_http_request__works(route: ApiRoute, input, expected):
    actual = route.get_http_request(request=input, base_url=DEFAULT_BASE_URL)
    assert actual.method == expected.method
    assert actual.url == expected.url
    assert actual.json == expected.json

    assert actual.params == expected.params


class ApiRequestConfigTests(BaseTest):
    def test__build__creates_from_nothing(self):
        self.set_env_vars((API_SERVICE_LOG_LEVEL_ENV_VAR, None))
        config1 = ApiRequestConfig.build()

        self.set_env_vars((API_SERVICE_LOG_LEVEL_ENV_VAR, "INFO"))
        config2 = ApiRequestConfig.build()

        expected_client_version = VersionStr("1.*")
        assert config1.client_version < expected_client_version
        assert config2.client_version < expected_client_version
        self.assertIsNone(config1.service_log_level)
        self.assertEqual(config2.service_log_level, "INFO")

    def test__to_headers__works(self):
        self.set_env_vars((API_SERVICE_LOG_LEVEL_ENV_VAR, None))
        config = ApiRequestConfig(VersionStr("1.0.0"), None)
        headers = config.to_headers()
        self.assertNotIn(API_SERVICE_LOG_LEVEL_KEY, headers)
        self.assertEqual(headers[CLIENT_VERSION_KEY], config.client_version)

    def test__from_headers__works(self):
        headers = {
            CLIENT_VERSION_KEY: "1.0.0",
            API_SERVICE_LOG_LEVEL_KEY: "INFO",
            "another-header": "another-value",
        }
        config = ApiRequestConfig.from_headers(headers)
        self.assertEqual(config.client_version, VersionStr("1.0.0"))
        self.assertEqual(config.service_log_level, "INFO")

    def build__client_version__fallback_to_client_version_package_name_default(self):
        class TestApiRequestConfig(ApiRequestConfig):
            client_version_default = None
            client_version_package_name_default = "aibs_informatics_core"

        expected_version = VersionStr(get_version("aibs_informatics_core"))

        self.assertEqual(TestApiRequestConfig.build__client_version(), expected_version)

    @mock.patch("aibs_informatics_core.models.api.route.get_version")
    def test__build__client_version__when_kwargs_and_env_vars_take_precedence(
        self, mock_get_version
    ):
        PACKAGE_A = "package_a"
        PACKAGE_B = "package_b"

        mock_get_version.side_effect = lambda x: {
            PACKAGE_A: "1.1.1",
            PACKAGE_B: "2.2.2",
        }[x]

        class TestApiRequestConfig(ApiRequestConfig):
            client_version_default = VersionStr("1.2.3")
            client_version_package_name_default = PACKAGE_A

        # client_version_default takes precedence over client_version_package_name_default
        self.assertEqual(TestApiRequestConfig.build__client_version(), VersionStr("1.2.3"))

        # client_version_package takes precedence over client_version_default when
        # set in env vars / kwargs
        self.assertEqual(
            TestApiRequestConfig.build__client_version(client_version_package_name=PACKAGE_B),
            VersionStr("2.2.2"),
        )

        # client_version takes precedence over rest when set in env vars / kwargs
        self.assertEqual(
            TestApiRequestConfig.build__client_version(client_version=VersionStr("4.5.6")),
            VersionStr("4.5.6"),
        )


class ApiRouteTests(BaseTest):
    def test__service_name__works(self):
        assert GetterResourceRoute.service_name() == "GetterResourceRoute"

    def test__get_http_parameters_from_request__fails_if_missing_data(self):
        class InvalidGetterResourceRoute(ApiRoute[BaseRequest, BaseResponse]):
            @classmethod
            def route_rule(cls) -> str:
                return "/test/<c>"

            @classmethod
            def route_method(cls) -> str:
                return "GET"

        with self.assertRaises(ValueError):
            InvalidGetterResourceRoute.get_http_parameters_from_request(BaseRequest(id_str="i"))

    def test__validate_headers__raises_error_for_stale_client_version(self):
        self.set_env_vars((API_SERVICE_LOG_LEVEL_ENV_VAR, None))
        with self.assertRaises(ValueError):
            GetterResourceRoute.validate_headers(
                {CLIENT_VERSION_KEY: "0.0.1", API_SERVICE_LOG_LEVEL_KEY: "INFO"},
                VersionStr("0.0.2"),
            )

    def test__resolve_request_config__works(self):
        config = GetterResourceRoute.resolve_request_config(
            {CLIENT_VERSION_KEY: "0.0.1", API_SERVICE_LOG_LEVEL_KEY: "INFO"}
        )
        assert config == ApiRequestConfig(VersionStr("0.0.1"), "INFO")

    def test__generate_headers__works(self):
        self.set_env_vars((API_SERVICE_LOG_LEVEL_ENV_VAR, None))

        GetterResourceRoute.generate_headers()

    def test__get_client_method_name__works(self):
        self.assertEqual(GetterResourceRoute.get_client_method_name(), "getter_resource")

    def test__create_client_method__works(self):
        # just testing that I can call it without error
        GetterResourceRoute.create_route_method()

    def test__repr__works(self):
        self.assertEqual(
            repr(GetterResourceRoute()), "GetterResourceRoute(rule=/test/resource, method=GET)"
        )
