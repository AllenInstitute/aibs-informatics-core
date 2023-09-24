from aibs_informatics_core.utils.units import (
    BYTES_PER_GIBIBYTE,
    BYTES_PER_KIBIBYTE,
    BYTES_PER_MEBIBYTE,
)


def test__units__work():
    assert BYTES_PER_KIBIBYTE == 1024
    assert BYTES_PER_MEBIBYTE == 1024**2
    assert BYTES_PER_GIBIBYTE == 1024**3
