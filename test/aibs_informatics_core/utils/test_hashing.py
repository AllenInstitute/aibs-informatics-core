import re
from test.base import BaseTest, does_not_raise
from typing import Optional, Pattern, Union

from pytest import mark, param, raises

from aibs_informatics_core.utils.hashing import (
    b64_decoded_str,
    b64_encoded_str,
    generate_path_hash,
    sha256_hexdigest,
    urlsafe_b64_decoded_str,
    urlsafe_b64_encoded_str,
    uuid_str,
)
from aibs_informatics_core.utils.json import JSON


@mark.parametrize(
    "value,expected,raises_error",
    [
        param(
            None,
            re.compile(r"([a-f\d]){64}"),
            does_not_raise(),
            id="No input creates unique hex digest each time",
        ),
        param(
            "1234",
            "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",
            does_not_raise(),
            id="string content creates deterministic hex digest",
        ),
        param(
            {},
            "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
            does_not_raise(),
            id="Empty dictionary content creates deterministic hex digest",
        ),
        param(
            {"c": "False", "b": {"b": True, "a": 1}, "a": [1, 2, {"a": 2}]},
            "3e81b965fd5209f8d90f77284482cbd8b06a2a2f60c25efb1cdfe119992674bb",
            does_not_raise(),
            id="nested dictionary content creates deterministic hex digest",
        ),
        param(
            123,
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            does_not_raise(),
            id="int content creates deterministic hex digest",
        ),
        param(
            False,
            "fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa",
            does_not_raise(),
            id="bool(False) content creates deterministic hex digest",
        ),
        param(
            True,
            "b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b",
            does_not_raise(),
            id="bool(True) content creates deterministic hex digest",
        ),
    ],
)
def test__sha256_hexdigest(value: Optional[JSON], expected: Union[str, Pattern], raises_error):

    with raises_error:
        actual = sha256_hexdigest(value)
        actual_again = sha256_hexdigest(value)

    if isinstance(expected, str):
        assert actual == expected
        assert actual_again == expected
    else:
        assert expected.fullmatch(actual) is not None
        assert expected.fullmatch(actual_again) is not None


def test__uuid_str__is_deterministic_only_with_same_input():
    assert uuid_str("123") == uuid_str("123")
    assert uuid_str("123") != uuid_str("1234")
    assert uuid_str() != uuid_str()


@mark.parametrize(
    "value,raises_error",
    [
        param(
            None,
            raises(AttributeError),
            id="No input raises error",
        ),
        param(
            "1234",
            does_not_raise(),
            id="string input is converted without issue",
        ),
        param(
            "{}",
            does_not_raise(),
            id="Empty dictionary content creates deterministic hex digest",
        ),
    ],
)
def test__b64_and_urlsafe_b64_encoder_decoder_functions__generate_original_value(
    value: str, raises_error
):

    with raises_error:
        b64_encoded_value = b64_encoded_str(value)
        b64_decoded_value = b64_decoded_str(b64_encoded_value)

        assert value == b64_decoded_value

        urlsafe_b64_encoded_value = urlsafe_b64_encoded_str(value)
        urlsafe_b64_decoded_value = urlsafe_b64_decoded_str(urlsafe_b64_encoded_value)

        assert value == urlsafe_b64_decoded_value


def test__b64_decoded_str__fails():
    with raises(Exception):
        b64_decoded_str("1234")


class HashingTests(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.asset_path = self.tmp_path()
        self.asset_path
        (self.asset_path / "a.py").write_text('a = "hello"')
        (self.asset_path / "b.py").write_text('b = "bye"')
        (self.asset_path / "x.txt").write_text("I'm a simple txt file")
        (self.asset_path / "dir1").mkdir(exist_ok=True)
        (self.asset_path / "dir1" / "__init__.py").touch()
        (self.asset_path / "dir1" / "a.py").write_text('a = "hello"')
        (self.asset_path / "dir1" / "b.py").write_text('b = "bye"')
        (self.asset_path / "dir1" / "c.py").write_text('c = ""')

    def test__generate_path_hash__changes_when_file_added_and_no_filters_applied(self):
        original_hash = generate_path_hash(self.asset_path)
        (self.asset_path / "c.py").write_text("c = 'hallo'")
        new_hash = generate_path_hash(str(self.asset_path))
        assert original_hash != new_hash

    def test__generate_path_hash__does_not_change_when_file_added_but_excluded(self):
        excludes = [r".*\.txt"]
        original_hash = generate_path_hash(str(self.asset_path), excludes=excludes)
        (self.asset_path / "dir1" / "c.txt").write_text("c = 'hallo'")
        new_hash = generate_path_hash(str(self.asset_path), excludes=excludes)
        assert original_hash == new_hash

    def test__generate_path_hash__does_not_change_when_file_added_but_not_included(
        self,
    ):
        includes = [r".*\.txt"]
        original_hash = generate_path_hash(str(self.asset_path), includes=includes)
        (self.asset_path / "c.py").write_text("c = 'hallo'")
        new_hash = generate_path_hash(str(self.asset_path), includes=includes)
        assert original_hash == new_hash

    def test__generate_path_hash__does_not_change_because_excludes_supersedes_includes(
        self,
    ):
        excludes = [r".*\.txt"]
        original_hash = generate_path_hash(
            str(self.asset_path), includes=excludes, excludes=excludes
        )
        (self.asset_path / "dir1" / "c.txt").write_text("c = 'hallo'")
        new_hash = generate_path_hash(str(self.asset_path), includes=excludes, excludes=excludes)
        assert original_hash == new_hash
