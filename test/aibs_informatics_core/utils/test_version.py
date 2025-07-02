from aibs_informatics_core.utils.version import get_version


def test__version__is_correct():
    # just checking major.minor version
    assert get_version("aibs_informatics_core").startswith("0.1.")
