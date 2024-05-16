from __future__ import annotations

import json
import logging
import os
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar, Union

from aibs_informatics_core.collections import PostInitMixin
from aibs_informatics_core.env import EnvBaseMixins
from aibs_informatics_core.models.aws.s3 import S3Path
from aibs_informatics_core.models.base import ModelProtocol
from aibs_informatics_core.utils.json import JSON, JSONObject, is_json_str, load_json_object

logger = logging.getLogger(__name__)


REQUEST = TypeVar("REQUEST", bound=ModelProtocol)
RESPONSE = TypeVar("RESPONSE", bound=ModelProtocol)

E = TypeVar("E", bound="BaseExecutor")


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
        Union[JSONObject, S3Path, str, Path, REQUEST]
            1. dict object
            2. S3 Path object (must implement s3 deserialization method)
            3. stringified object
            4. path to file of json object

        Args:
            request (Union[JSONObject, S3Path, str, Path]): raw request

        Returns:
            REQUEST: Deserialized request
        """
        if isinstance(request, cls.get_request_cls()):
            return request

        request = cls.load_input(request)
        if isinstance(request, dict):
            try:
                return cls.get_request_cls().from_dict(request)
            except Exception as e:
                logger.error(f"Could not deserialize object. error: {e}")
                raise e
        else:
            raise ValueError(f"Cannot deserialize request: {request}, type: {type(request)}")

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
    def load_input(cls, input: Any) -> JSON:
        """Loads input from various sources

        Supported input types:
            1. dict object
            2. S3 Path object (must implement s3 deserialization method)
            3. stringified object
            4. path to file of json object

        Args:
            input (Any): raw input. Can be any of the supported types.

        Returns:
            JSON: content loaded from input
        """
        if isinstance(input, dict):
            return input
        elif isinstance(input, str) and is_json_str(input):
            return load_json_object(input)
        elif isinstance(input, S3Path) or (isinstance(input, str) and S3Path.is_valid(input)):
            return cls.load_input__remote(S3Path(input))
        elif isinstance(input, (str, Path)):
            return cls.load_input__file(Path(input))
        else:
            raise ValueError(f"Cannot read input: {input}, type: {type(input)}")

    @classmethod
    def load_input__remote(cls, remote_path: S3Path) -> JSON:
        """Reads input from S3 location

        Args:
            s3_path (S3Path): S3 location to read input from

        Returns:
            JSON: JSON data read from S3
        """
        raise NotImplementedError(
            f"{cls.__name__} has not provided an implementation for this form of input"
        )

    @classmethod
    def load_input__file(cls, local_path: Path) -> JSON:
        """Reads input from file

        Args:
            local_path (Path): Local path to read input from

        Returns:
            JSON: JSON data read from file
        """
        if not local_path.exists():
            raise ValueError(f"local path specified {local_path} does not exist")
        if local_path.is_dir():
            raise ValueError(f"local path specified {local_path} cannot be read. Must be a file.")
        return load_json_object(local_path)

    @classmethod
    def write_output(cls, output: JSON, path: Union[str, Path]) -> None:
        """Writes output to location

        Args:
            output (JSON): serialized output object
            path (Path | str): location to write output to. Can be S3 or local file
        """

        if isinstance(path, S3Path) or (isinstance(path, str) and S3Path.is_valid(path)):
            return cls.write_output__remote(output, S3Path(path))
        else:
            # Here we assume that it could be string or path to file
            return cls.write_output__file(output, Path(path))

    @classmethod
    def write_output__remote(cls, output: JSON, remote_path: S3Path) -> None:
        """Writes output to Remote location

        Args:
            output (RESPONSE): output object
            remote_path (S3Path): S3 location to write response to
        """
        raise NotImplementedError(
            f"{cls.__name__} has not provided an implementation for this form of serialization"
        )

    @classmethod
    def write_output__file(cls, output: JSON, local_path: Path) -> None:
        """Writes output to file

        Args:
            output (JSON): serialized output json
            local_path (S3Path): Local path to write response to
        """

        if local_path.is_dir() or (
            local_path.parent.exists() and not os.access(local_path.parent, os.W_OK)
        ):
            raise ValueError(
                f"local path specified {local_path} cannot be written to. " f"Must be a file "
            )
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(json.dumps(output, sort_keys=True))

    @classmethod
    def get_executor_name(cls) -> str:
        """Returns a distinguishable name of the executor class

        By default, it returns class name.

        """
        return cls.__name__

    @classmethod
    def build_from_env(cls: Type[E], **kwargs) -> E:
        """Creates an executor from environment

        Must be able to create an executor from environment variables

        Returns:
            E: Executor object
        """
        return cls(**kwargs)

    @classmethod
    def run_executor(
        cls, input: JSON, output_location: Optional[Union[str, Path]] = None, **kwargs
    ) -> Optional[JSON]:
        """Runs an executor

        Args:
            input (JSON): input to executor
            output_location (Optional[str], optional): Optional output location to write response to. Defaults to None.
        """
        executor = cls.build_from_env(**kwargs)

        request = cls.deserialize_request(input)
        response = executor.handle(request)
        output = executor.serialize_response(response) if response else None

        if output_location:
            if output is None:
                logger.warning(
                    "Response is None but output location is specified. Writing empty dict"
                )
            executor.write_output(output or {}, output_location)

        return output
