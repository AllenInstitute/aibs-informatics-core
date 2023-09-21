import unittest

from aibs_informatics_core.utils.tools.dict_helpers import (
    convert_key_case,
    flatten_dict,
    nested_dict,
    remove_null_values,
)


class DictUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.data_nested1 = {
            "key1": {
                "subkey1": "value1",
                "subkey2": "value2",
            },
            "key2": {
                "subkey3": "value3",
                "subkey4": "value4",
            },
        }

        self.data_flat1 = {
            "key1.subkey1": "value1",
            "key1.subkey2": "value2",
            "key2.subkey3": "value3",
            "key2.subkey4": "value4",
        }

        self.data_nested2 = {
            "key1": {
                "subkey1": "value1",
                "subkey2": {
                    "subsubkey1": "value2",
                },
            },
            "key2": {
                "subkey3": "value3",
                "subkey4": "value4",
            },
        }

        self.data_flat2 = {
            "key1.subkey1": "value1",
            "key1.subkey2.subsubkey1": "value2",
            "key2.subkey3": "value3",
            "key2.subkey4": "value4",
        }

    def test__remove_null_values__removes_top_level_nulls_and_returns_copy(self):
        original = dict(a=None, b=False, c=dict(a=None, b=1))
        expected = dict(b=False, c=dict(a=None, b=1))
        result = remove_null_values(original)
        self.assertDictEqual(expected, result)
        self.assertIsNot(original, result)

    def test__remove_null_values__removes_all_nulls_and_returns_copy(self):
        original = dict(a=None, b=False, c=dict(a=None, b=1))
        expected = dict(b=False, c=dict(b=1))
        result = remove_null_values(original, in_place=False, recursive=True)
        self.assertDictEqual(expected, result)
        self.assertIsNot(original, result)

    def test__remove_null_values__removes_all_nulls_in_place(self):
        original = dict(a=None, b=False, c=dict(a=None, b=1))
        expected = dict(b=False, c=dict(b=1))
        result = remove_null_values(original, in_place=True, recursive=True)
        self.assertDictEqual(expected, result)
        self.assertIs(original, result)

    def test__nested_dict__case1(self):
        result = nested_dict(self.data_flat1, delimiter=".")
        self.assertEqual(result, self.data_nested1)

    def test__nested_dict__case2(self):
        result = nested_dict(self.data_flat2, delimiter=".")
        self.assertEqual(result, self.data_nested2)

    def test__nested_dict__collision_causes_failure(self):
        data_with_collision = {
            "key1.subkey1": "value1",
            "key1": "value2",
        }
        with self.assertRaises(ValueError):
            nested_dict(data_with_collision, delimiter=".")

    def test__flatten_dict__case1(self):
        result = flatten_dict(self.data_nested1, delimiter=".")
        self.assertEqual(result, self.data_flat1)

    def test__flatten_dict__case2(self):
        result = flatten_dict(self.data_nested2, delimiter=".")
        self.assertEqual(result, self.data_flat2)

    def test__nested_dict__flatten_dict__handles_empty(self):
        data = {}
        result = nested_dict(data, delimiter=".")
        self.assertEqual(result, {})
        result = flatten_dict(data, delimiter=".")
        self.assertEqual(result, {})

    def test_nested_dict__flatten_dict__handles_single_level_dict(self):
        data = {"key1": "value1", "key2": "value2"}
        result = nested_dict(data, delimiter=".")
        self.assertEqual(result, data)
        result = flatten_dict(data, delimiter=".")
        self.assertEqual(result, data)

    def test_nested_dict__flatten_dict__handles_different_delimiter(self):
        data_nested = {"key1": {"subkey1": "value1"}}
        data_flat = {"key1-subkey1": "value1"}
        result = nested_dict(data_flat, delimiter="-")
        self.assertEqual(result, data_nested)
        result = flatten_dict(data_nested, delimiter="-")
        self.assertEqual(result, data_flat)


def test_convert_key_case_with_dict():
    data = {"testKey1": "value1", "testKey2": "value2"}
    expected = {"TESTKEY1": "value1", "TESTKEY2": "value2"}
    assert convert_key_case(data, str.upper) == expected


def test_convert_key_case_with_nested_dict():
    data = {"testKey1": "value1", "nestedDict": {"testKey2": "value2"}}
    expected = {"TESTKEY1": "value1", "NESTEDDICT": {"TESTKEY2": "value2"}}
    assert convert_key_case(data, str.upper) == expected


def test_convert_key_case_with_list():
    data = [{"testKey1": "value1"}, {"testKey2": "value2"}]
    expected = [{"TESTKEY1": "value1"}, {"TESTKEY2": "value2"}]
    assert convert_key_case(data, str.upper) == expected


def test_convert_key_case_with_non_collection():
    data = "testKey"
    expected = "testKey"
    assert convert_key_case(data, str.upper) == expected
