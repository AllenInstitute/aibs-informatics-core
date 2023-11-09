import json
from dataclasses import dataclass
from test.base import BaseTest
from typing import Optional

from aibs_informatics_core.executors import BaseExecutor, run_cli_executor
from aibs_informatics_core.models.aws.s3 import S3Path
from aibs_informatics_core.models.base import SchemaModel
from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.modules import get_qualified_name


@dataclass
class NoOpRequest(SchemaModel):
    any_string: str
    any_int: int
    include_response: bool


class NoOpExecutor(BaseExecutor[NoOpRequest, NoOpRequest]):
    def handle(self, request: NoOpRequest) -> Optional[NoOpRequest]:
        if request.include_response:
            return request
        return None

    @classmethod
    def load_input__remote(cls, remote_path: S3Path) -> JSON:
        return {"any_string": "any_string", "any_int": 123, "include_response": True}

    @classmethod
    def write_output__remote(cls, output: JSON, remote_path: S3Path) -> None:
        return None


class BaseExecutorTests(BaseTest):
    def test__get_executor_name__returns_correct_name(self):
        actual = NoOpExecutor.get_executor_name()
        self.assertEqual(actual, "NoOpExecutor")

    def test__get_response_cls__returns_correct_class(self):
        actual = NoOpExecutor.get_response_cls()
        self.assertEqual(actual, NoOpRequest)

    def test__deserialize_request__handles_dict(self):
        request = NoOpRequest("any_string", 123, False)

        actual_request = NoOpExecutor.deserialize_request(request.to_dict())
        self.assertEqual(request, actual_request)

    def test__deserialize_request__handles_string(self):
        request = NoOpRequest("any_string", 123, False)

        actual_request = NoOpExecutor.deserialize_request(request.to_json())
        self.assertEqual(request, actual_request)

    def test__deserialize_request__handles_object(self):
        request = NoOpRequest("any_string", 123, False)

        actual_request = NoOpExecutor.deserialize_request(request)
        self.assertEqual(request, actual_request)

    def test__deserialize_request__handles_remote(self):
        request = NoOpRequest("any_string", 123, True)

        actual_request = NoOpExecutor.deserialize_request("s3://bucket/key")
        self.assertEqual(request, actual_request)

    def test__deserialize_request__handles_local(self):
        request = NoOpRequest("any_string", 123, True)

        local_path = self.tmp_file(content=request.to_json())
        actual_request = NoOpExecutor.deserialize_request(local_path)
        self.assertEqual(request, actual_request)

    def test__deserialize_request__does_not_handle_invalid_dict(self):
        with self.assertRaises(TypeError):
            NoOpExecutor.deserialize_request("{}")

    def test__deserialize_request__does_not_handle_list(self):
        with self.assertRaises(ValueError):
            NoOpExecutor.deserialize_request([])

    def test__load_input__fails_for_invalid_type(self):
        with self.assertRaises(ValueError):
            NoOpExecutor.load_input(TypeError())

    def test__load_input__fails_for_invalid_path(self):
        with self.assertRaises(ValueError):
            NoOpExecutor.load_input("path/to/nowhere")

        with self.assertRaises(ValueError):
            NoOpExecutor.load_input(self.tmp_path())

    def test__write_output__fails_for_invalid_path(self):
        with self.assertRaises(ValueError):
            # Directory
            NoOpExecutor.write_output({}, self.tmp_path())

    def test__write_output__writes_to_file(self):
        local_path = self.tmp_file()
        NoOpExecutor.write_output({}, local_path)
        assert local_path.read_text() == "{}"

    def test__write_output__writes_to_s3(self):
        s3_path = S3Path("s3://bucket/key")
        NoOpExecutor.write_output({}, s3_path)

    def test__serialize_response__works(self):
        request = NoOpRequest("any_string", 123, False)

        response = NoOpExecutor.serialize_response(request)
        self.assertDictEqual(request.to_dict(), response)

    def test__handle__returns_no_response(self):
        request = NoOpRequest("any_string", 123, False)

        response = NoOpExecutor().handle(request)
        self.assertIsNone(response)

    def test__handle__returns_response(self):
        request = NoOpRequest("any_string", 123, True)

        response = NoOpExecutor().handle(request)
        self.assertEqual(request, response)

    def test__run_executor__handles_no_response__no_output_location(self):
        request = NoOpRequest("any_string", 123, False)

        response = NoOpExecutor.run_executor(request.to_dict())
        self.assertIsNone(response)

    def test__run_executor__handles_no_response__with_output_location(self):
        request = NoOpRequest("any_string", 123, False)
        output_path = self.tmp_file()
        response = NoOpExecutor.run_executor(request.to_dict(), output_path)
        self.assertIsNone(response)
        assert output_path.read_text() == "{}"

    def test__run_executor__handles_response__no_output_location(self):
        request = NoOpRequest("any_string", 123, True)
        response = NoOpExecutor.run_executor(request.to_dict())
        self.assertEqual(request.to_dict(), response)

    def test__run_executor__handles_response__with_output_location(self):
        request = NoOpRequest("any_string", 123, True)
        output_path = self.tmp_file()
        response = NoOpExecutor.run_executor(request.to_dict(), output_path)
        self.assertEqual(request.to_dict(), response)
        self.assertDictEqual(json.loads(output_path.read_text()), request.to_dict())


class RunCliExecutorTests(BaseTest):
    def test__run_cli_executor__handles_simple_case(self):
        request = NoOpRequest("any_string", 123, True)
        executor_name = get_qualified_name(NoOpExecutor)

        output_path = self.tmp_file()

        args = [
            "--executor",
            executor_name,
            "--input",
            json.dumps(request.to_dict()),
            "--output-location",
            output_path.as_posix(),
        ]
        run_cli_executor(args)

        self.assertDictEqual(json.loads(output_path.read_text()), request.to_dict())

    def test__run_cli_executor__fails_for_invalid_executor(self):
        request = NoOpRequest("any_string", 123, True)

        output_path = self.tmp_file()
        args = [
            "--executor",
            get_qualified_name(NoOpRequest),
            "--input",
            json.dumps(request.to_dict()),
            "--output-location",
            output_path.as_posix(),
        ]
        with self.assertRaises(ValueError):
            run_cli_executor(args)
