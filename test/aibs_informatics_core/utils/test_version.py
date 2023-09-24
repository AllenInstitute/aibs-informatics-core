from aibs_informatics_core.utils.version import get_version


def test__version__is_correct():
    assert get_version("aibs_informatics_core") == "0.0.1"
