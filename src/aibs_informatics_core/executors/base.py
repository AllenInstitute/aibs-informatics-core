import logging
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Optional, Type, TypeVar

from aibs_informatics_core.collections import PostInitMixin
from aibs_informatics_core.env import EnvBaseMixins
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.base import ModelProtocol
from aibs_informatics_core.utils.json import JSON, JSONObject, load_json_object

logger = logging.getLogger(__name__)


REQUEST = TypeVar("REQUEST", bound=ModelProtocol)
RESPONSE = TypeVar("RESPONSE", bound=ModelProtocol)


@dataclass  # type: ignore[misc] # mypy #5374
class BaseExecutor(EnvBaseMixins, PostInitMixin, Generic[REQUEST, RESPONSE]):
    @abstractmethod
    def handle(self, request: REQUEST) -> Optional[RESPONSE]:  # pragma: no cover
        """Core logic for handling request

        NOT IMPLEMENTED

        Args:
            request (API_REQUEST): Request object expected

        Returns:
            Optional[API_RESPONSE]: response object returned, Optional
        """
        raise NotImplementedError("Must implement handler logic here")

    # --------------------------------------------------------------------
    # Request & Response De-/Serialization
    # --------------------------------------------------------------------

    @classmethod
    def get_request_cls(cls) -> Type[REQUEST]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore

    @classmethod
    def get_response_cls(cls) -> Type[RESPONSE]:
        return cls.__orig_bases__[0].__args__[1]  # type: ignore

    @classmethod
    def deserialize_request(cls, request: JSON) -> REQUEST:
        """Deserialize a raw request

        Supported request types:
        Union[JSONObject, S3URI, str, Path, REQUEST]
            1. dict object
            2. S3 Path object (must implement s3 deserialization method)
            3. stringified object
            4. path to file of json object

        Args:
            request (Union[JSONObject, S3URI, str, Path]): raw request

        Returns:
            REQUEST: Deserialized request
        """
        if isinstance(request, dict):
            return cls.deserialize_request__dict(request)
        elif isinstance(request, S3URI) or (isinstance(request, str) and S3URI.is_valid(request)):
            return cls.deserialize_request__s3(S3URI(request))
        elif isinstance(request, (str, Path)):
            # Here we assume that it could be string or path to file
            return cls.deserialize_request__dict(load_json_object(request))
        if isinstance(request, cls.get_request_cls()):
            return request
        else:
            raise ValueError(f"Cannot deserialize request: {request}, type: {type(request)}")

    @classmethod
    def deserialize_request__dict(cls, request_dict: JSONObject) -> REQUEST:
        """Deserialize a request from a request JSON object

        Args:
            request_dict (JSON): serialized JSON object representing request

        Returns:
            API_REQUEST: Request object
        """
        try:
            return cls.get_request_cls().from_dict(request_dict)
        except Exception as e:
            logger.error(f"Could not deserialize object. error: {e}")
            raise e

    @classmethod
    def deserialize_request__s3(cls, request_path: S3URI) -> REQUEST:
        """Deserialize a request from a serialized request object stored at s3 location

        Args:
            request_path (S3URI): S3 path to serialized request object

        Returns:
            REQUEST: a deserialized request object
        """
        raise NotImplementedError(
            f"{cls.__name__} has not provided an implementation for this form of deserialization."
        )

    @classmethod
    def serialize_response(cls, response: RESPONSE) -> JSONObject:
        """Serializes response object into JSON

        Args:
            response (API_RESPONSE): The returned response object

        Returns:
            JSON: serialized form of response object
        """
        return response.to_dict()

    @classmethod
    def get_executor_name(cls) -> str:
        """Returns a distinguishable name of the executor class

        By default, it returns class name.

        """
        return cls.__name__
