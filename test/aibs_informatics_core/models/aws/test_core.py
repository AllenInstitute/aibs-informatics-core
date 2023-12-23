from aibs_informatics_test_resources import does_not_raise
from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.core import AWSAccountId, AWSRegion


@mark.parametrize(
    "account_id_string, raise_expectation",
    [
        param("1234567890", does_not_raise(), id="1234567890 (min)"),
        param("123456789012", does_not_raise(), id="123456789012 (max)"),
        param("123456a7890", raises(ValidationError), id="invalid: too short"),
        param("12345678901234", raises(ValidationError), id="invalid: too long"),
        param("12345678901a", raises(ValidationError), id="invalid: contains non-digit"),
    ],
)
def test__AWSAccountId__validation(account_id_string, raise_expectation):
    with raise_expectation:
        AWSAccountId(account_id_string)


@mark.parametrize(
    "region_string, raise_expectation",
    [
        param("us-east-2", does_not_raise(), id="us-east-2"),
        param("us-east-1", does_not_raise(), id="us-east-1"),
        param("us-west-1", does_not_raise(), id="us-west-1"),
        param("us-west-2", does_not_raise(), id="us-west-2"),
        param("ap-east-1", does_not_raise(), id="ap-east-1"),
        param("ap-south-1", does_not_raise(), id="ap-south-1"),
        param("ap-northeast-2", does_not_raise(), id="ap-northeast-2"),
        param("ap-southeast-1", does_not_raise(), id="ap-southeast-1"),
        param("ap-southeast-2", does_not_raise(), id="ap-southeast-2"),
        param("ap-northeast-1", does_not_raise(), id="ap-northeast-1"),
        param("ca-central-1", does_not_raise(), id="ca-central-1"),
        param("cn-north-1", does_not_raise(), id="cn-north-1"),
        param("cn-northwest-1", does_not_raise(), id="cn-northwest-1"),
        param("eu-central-1", does_not_raise(), id="eu-central-1"),
        param("eu-west-1", does_not_raise(), id="eu-west-1"),
        param("eu-west-2", does_not_raise(), id="eu-west-2"),
        param("eu-west-3", does_not_raise(), id="eu-west-3"),
        param("eu-north-1", does_not_raise(), id="eu-north-1"),
        param("sa-east-1", does_not_raise(), id="sa-east-1"),
        param("us-gov-east-1", does_not_raise(), id="us-gov-east-1"),
        param("us-gov-west-1", does_not_raise(), id="us-gov-west-1"),
        param("useast-2", raises(ValidationError), id="invalid: missing dash"),
        param("useast2", raises(ValidationError), id="invalid: missing dashes"),
    ],
)
def test__AWSRegion__validation(region_string, raise_expectation):
    with raise_expectation:
        AWSRegion(region_string)
