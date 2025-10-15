import decimal
import json
from pathlib import Path
from typing import Union

from aibs_informatics_core.utils.json import JSON, DecimalEncoder, load_json, load_json_object
from test.base import BaseTest


class DecimalEncoderTests(BaseTest):
    def test__encodes_decimal_properly(self):
        dict_with_decimal = dict(decimal_value=decimal.Decimal(1.0))
        actual = json.dumps(dict_with_decimal, cls=DecimalEncoder)
        self.assertEqual(actual, '{"decimal_value": "1"}')


class JsonUtilTests(BaseTest):
    def dump_json(self, data: JSON, to_file: bool = False) -> Union[str, Path]:
        json_string = json.dumps(data)
        if to_file:
            tmp_file = self.tmp_file()
            tmp_file.write_text(json_string)
            return tmp_file
        else:
            return json_string

    def test__load_json__successfully_loads_stringified_dict(self):
        data = dict(a=1, b=2)
        self.assertJsonEqual(data, load_json(self.dump_json(data)))

    def test__load_json__successfully_loads_stringified_list(self):
        data = [dict(a=1, b=2)]
        self.assertJsonEqual(data, load_json(self.dump_json(data)))

    def test__load_json__successfully_loads_path(self):
        data = dict(a=1, b=2)
        self.assertJsonEqual(data, load_json(self.dump_json(data, to_file=True)))

    def test__load_json__successfully_loads_str_path(self):
        data = dict(a=1, b=2)
        self.assertJsonEqual(data, load_json(str(self.dump_json(data, to_file=True))))

    def test__load_json__fails_to_load_invalid_str(self):
        data = "hello"
        with self.assertRaises(ValueError):
            load_json(data)

    def test__load_json__fails_to_load_invalid_str_at_path(self):
        tmp_file = self.tmp_file()
        tmp_file.write_text("notjson")
        with self.assertRaises(ValueError):
            load_json(tmp_file)

    def test__load_json__fails_to_load_invalid_str_path(self):
        tmp_file = self.tmp_file()
        with self.assertRaises(ValueError):
            load_json(str(tmp_file))

    def test__load_json__successfully_loads_str_dict(self):
        data = dict(a=1, b=2)
        self.assertJsonEqual(data, load_json_object(str(self.dump_json(data))))

    def test__load_json__fails_explicitly_for_non_dict_json(self):
        with self.assertRaises(ValueError):
            load_json_object(self.dump_json([dict(a=1, b=2)]))
