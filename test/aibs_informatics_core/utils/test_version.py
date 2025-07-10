from aibs_informatics_core.utils.version import get_version


def test__version__is_correct():
    # just checking major version
    assert get_version("aibs_informatics_test_resources").startswith("0.")
