from pytest import mark, param, raises

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.email_address import EmailAddress
from test.base import does_not_raise


@mark.parametrize(
    "input_value, expected, raise_expectation",
    [
        param(
            "simple@abc.com",
            EmailAddress("simple@abc.com"),
            does_not_raise(),
            id="Test simple email address",
        ),
        param(
            "marmotdev+subscription@alleninstitute.org",
            EmailAddress("marmotdev+subscription@alleninstitute.org"),
            does_not_raise(),
            id="Test email address with +",
        ),
        param(
            "invalid email address@someplace.com",
            None,
            raises(ValidationError),
            id="Test invalid email address",
        ),
    ],
)
def test_email_address_instantiation(input_value, expected, raise_expectation):
    with raise_expectation:
        actual = EmailAddress(input_value)
    if expected:
        assert expected == actual
