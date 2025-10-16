from contextlib import nullcontext as does_not_raise
from typing import Optional

from pytest import mark, param, raises

from aibs_informatics_core.models.aws.iam import IAMArn, IAMRoleArn, PrincipalType, UserId


@mark.parametrize(
    "value, expected, expected_principal_type, raise_expectation",
    [
        param(
            "123456789012",
            UserId("123456789012"),
            PrincipalType.Account,
            does_not_raise(),
            id="Account UserId",
        ),
        param(
            "AIDACKCEVSQ6C2EXAMPLE",
            UserId("AIDACKCEVSQ6C2EXAMPLE"),
            PrincipalType.User,
            does_not_raise(),
            id="User UserId",
        ),
        param(
            "123456789012:some-user",
            UserId("123456789012:some-user"),
            PrincipalType.FederatedUser,
            does_not_raise(),
            id="FederatedUser UserId",
        ),
        param(
            "AIDACKCEVSQ6C2EXAMPLE:some-person@company.com",
            UserId("AIDACKCEVSQ6C2EXAMPLE:some-person@company.com"),
            PrincipalType.AssumedRole,
            does_not_raise(),
            id="AssumedRole UserId (Web/SAML/regular)",
        ),
        param(
            "AIDACKCEVSQ6C2EXAMPLE:i-abcdef1234",
            UserId("AIDACKCEVSQ6C2EXAMPLE:i-abcdef1234"),
            PrincipalType.AssumedRole,
            does_not_raise(),
            id="AssumedRole UserId (ec2)",
        ),
        param(
            "anonymous",
            UserId("anonymous"),
            PrincipalType.Anonymous,
            does_not_raise(),
            id="Anonymous UserId",
        ),
        param("xyz", None, None, raises(ValueError), id="Invalid UserId"),
        param("1234567890", None, None, raises(ValueError), id="Invalid account UserId"),
    ],
)
def test__UserId__validates(
    value: str,
    expected: Optional[UserId],
    expected_principal_type: Optional[PrincipalType],
    raise_expectation,
):
    with raise_expectation:
        actual = UserId(value)

    if expected:
        assert actual == expected
        assert actual.principal_type == expected_principal_type


@mark.parametrize(
    "value, expected_account_id, expected_resource, expected_resource_type, expected_resource_id, expected_resource_name, expected_resource_path, raise_expectation",  # noqa: E501
    [
        param(
            "arn:aws:iam::123456789012:root",
            "123456789012",
            "root",
            "root",
            "123456789012",
            "123456789012",
            "/",
            does_not_raise(),
            id="Account IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:user/JohnDoe",
            "123456789012",
            "user/JohnDoe",
            "user",
            "JohnDoe",
            "JohnDoe",
            "/",
            does_not_raise(),
            id="User IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:user/division_abc/subdivision_xyz/JaneDoe",
            "123456789012",
            "user/division_abc/subdivision_xyz/JaneDoe",
            "user",
            "division_abc/subdivision_xyz/JaneDoe",
            "JaneDoe",
            "/division_abc/subdivision_xyz",
            does_not_raise(),
            id="User subdivision IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:group/Developers",
            "123456789012",
            "group/Developers",
            "group",
            "Developers",
            "Developers",
            "/",
            does_not_raise(),
            id="Group IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:group/division_abc/subdivision_xyz/product_A/Developers",
            "123456789012",
            "group/division_abc/subdivision_xyz/product_A/Developers",
            "group",
            "division_abc/subdivision_xyz/product_A/Developers",
            "Developers",
            "/division_abc/subdivision_xyz/product_A",
            does_not_raise(),
            id="Group subdivision IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/S3Access",
            "123456789012",
            "role/S3Access",
            "role",
            "S3Access",
            "S3Access",
            "/",
            does_not_raise(),
            id="Role IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/application_abc/component_xyz/RDSAccess",
            "123456789012",
            "role/application_abc/component_xyz/RDSAccess",
            "role",
            "application_abc/component_xyz/RDSAccess",
            "RDSAccess",
            "/application_abc/component_xyz",
            does_not_raise(),
            id="Role subdivision IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer",
            "123456789012",
            "role/aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer",
            "role",
            "aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer",
            "AWSServiceRoleForAccessAnalyzer",
            "/aws-service-role/access-analyzer.amazonaws.com",
            does_not_raise(),
            id="AWS Service Role (with endpoint) IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/service-role/QuickSightAction",
            "123456789012",
            "role/service-role/QuickSightAction",
            "role",
            "service-role/QuickSightAction",
            "QuickSightAction",
            "/service-role",
            does_not_raise(),
            id="AWS Service Role IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:policy/UsersManageOwnCredentials",
            "123456789012",
            "policy/UsersManageOwnCredentials",
            "policy",
            "UsersManageOwnCredentials",
            "UsersManageOwnCredentials",
            "/",
            does_not_raise(),
            id="Policy IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:policy/division_abc/subdivision_xyz/UsersManageOwnCredentials",
            "123456789012",
            "policy/division_abc/subdivision_xyz/UsersManageOwnCredentials",
            "policy",
            "division_abc/subdivision_xyz/UsersManageOwnCredentials",
            "UsersManageOwnCredentials",
            "/division_abc/subdivision_xyz",
            does_not_raise(),
            id="Policy subdivision IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:instance-profile/Webserver",
            "123456789012",
            "instance-profile/Webserver",
            "instance-profile",
            "Webserver",
            "Webserver",
            "/",
            does_not_raise(),
            id="Instance profile IAMArn",
        ),
        param(
            "arn:aws:sts::123456789012:federated-user/JohnDoe",
            "123456789012",
            "federated-user/JohnDoe",
            "federated-user",
            "JohnDoe",
            "JohnDoe",
            "/",
            does_not_raise(),
            id="Federated User IAMArn",
        ),
        param(
            "arn:aws:sts::123456789012:assumed-role/Accounting-Role/JaneDoe",
            "123456789012",
            "assumed-role/Accounting-Role/JaneDoe",
            "assumed-role",
            "Accounting-Role/JaneDoe",
            "JaneDoe",
            "/Accounting-Role",
            does_not_raise(),
            id="Assumed role IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:mfa/JaneDoeMFA",
            "123456789012",
            "mfa/JaneDoeMFA",
            "mfa",
            "JaneDoeMFA",
            "JaneDoeMFA",
            "/",
            does_not_raise(),
            id="MFA IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:u2f/user/JohnDoe/default (U2F security key)",
            "123456789012",
            "u2f/user/JohnDoe/default (U2F security key)",
            "u2f",
            "user/JohnDoe/default (U2F security key)",
            "default (U2F security key)",
            "/user/JohnDoe",
            does_not_raise(),
            id="U2F IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:server-certificate/ProdServerCert",
            "123456789012",
            "server-certificate/ProdServerCert",
            "server-certificate",
            "ProdServerCert",
            "ProdServerCert",
            "/",
            does_not_raise(),
            id="Server Certificate IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:server-certificate/division_abc/subdivision_xyz/ProdServerCert",
            "123456789012",
            "server-certificate/division_abc/subdivision_xyz/ProdServerCert",
            "server-certificate",
            "division_abc/subdivision_xyz/ProdServerCert",
            "ProdServerCert",
            "/division_abc/subdivision_xyz",
            does_not_raise(),
            id="Server Certificate subdivision IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:saml-provider/ADFSProvider",
            "123456789012",
            "saml-provider/ADFSProvider",
            "saml-provider",
            "ADFSProvider",
            "ADFSProvider",
            "/",
            does_not_raise(),
            id="SAML Provider IAMArn",
        ),
        param(
            "arn:aws:iam::123456789012:oidc-provider/GoogleProvider",
            "123456789012",
            "oidc-provider/GoogleProvider",
            "oidc-provider",
            "GoogleProvider",
            "GoogleProvider",
            "/",
            does_not_raise(),
            id="OIDC Provider IAMArn",
        ),
    ],
)
def test__IAMArn__validates(
    value: str,
    expected_account_id: Optional[str],
    expected_resource: Optional[str],
    expected_resource_type: Optional[str],
    expected_resource_id: Optional[str],
    expected_resource_name: Optional[str],
    expected_resource_path: Optional[str],
    raise_expectation,
):
    with raise_expectation:
        actual = IAMArn(value)

        assert actual.account_id == expected_account_id
        assert actual.resource == expected_resource
        assert actual.resource_type == expected_resource_type
        assert actual.resource_id == expected_resource_id
        assert actual.resource_name == expected_resource_name
        assert actual.resource_path == expected_resource_path


@mark.parametrize(
    "value, expected_account_id, expected_resource_id, expected_role_name, expected_role_path, raise_expectation",  # noqa: E501
    [
        param(
            "arn:aws:iam::123456789012:role/MyRole",
            "123456789012",
            "MyRole",
            "MyRole",
            "/",
            does_not_raise(),
            id="Simple IAMRoleArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/service-role/MyServiceRole",
            "123456789012",
            "service-role/MyServiceRole",
            "MyServiceRole",
            "/service-role",
            does_not_raise(),
            id="Service role IAMRoleArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer",
            "123456789012",
            "aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer",
            "AWSServiceRoleForAccessAnalyzer",
            "/aws-service-role/access-analyzer.amazonaws.com",
            does_not_raise(),
            id="Service linked IAMRoleArn",
        ),
        param(
            "arn:aws:iam::123456789012:user/JohnDoe",
            None,
            None,
            None,
            None,
            raises(ValueError),
            id="Non role IAMRoleArn",
        ),
        param(
            "arn:aws:iam::123456789012:role/",
            None,
            None,
            None,
            None,
            raises(ValueError),
            id="Missing role name IAMRoleArn",
        ),
    ],
)
def test__IAMRoleArn__validates(
    value: str,
    expected_account_id: Optional[str],
    expected_resource_id: Optional[str],
    expected_role_name: Optional[str],
    expected_role_path: Optional[str],
    raise_expectation,
):
    with raise_expectation:
        actual = IAMRoleArn(value)

        assert actual.account_id == expected_account_id
        assert actual.resource_id == expected_resource_id
        assert actual.role_name == expected_role_name
        assert actual.role_path == expected_role_path
