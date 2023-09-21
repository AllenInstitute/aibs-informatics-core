from dataclasses import dataclass
from test.base import BaseTest
from typing import Optional

from aibs_informatics_core.executors.base import BaseExecutor
from aibs_informatics_core.models.base import SchemaModel


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


class TestBaseExecutor(BaseTest):
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

    def test__deserialize_request__does_not_handle_invalid_dict(self):

        with self.assertRaises(Exception):
            NoOpExecutor.deserialize_request("{}")

    def test__deserialize_request__does_not_handle_s3_by_default(self):
        with self.assertRaises(NotImplementedError):
            NoOpExecutor.deserialize_request("s3://blah/blah")

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
