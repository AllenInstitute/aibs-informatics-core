import json
import logging
import os
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Optional, Type, TypeVar, Union

from aibs_informatics_core.collections import PostInitMixin
from aibs_informatics_core.env import EnvBaseMixins
from aibs_informatics_core.executors.base import BaseExecutor
from aibs_informatics_core.models.aws.s3 import S3Path
from aibs_informatics_core.models.base import ModelProtocol
from aibs_informatics_core.utils.json import JSON, JSONObject, is_json_str, load_json_object
from aibs_informatics_core.utils.modules import load_type_from_qualified_name

logger = logging.getLogger(__name__)


def get_cli_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Executor CLI")

    parser.add_argument(
        "--executor",
        dest="executor",
        required=True,
        help=(
            f"executor class to run. Must be a fully qualified name of the executor class. "
            f"e.g. aibs_informatics_aws_lambda.common.executor.BaseExecutor"
        ),
    )
    parser.add_argument(
        "--input",
        "--request",
        "-i",
        dest="request",
        required=True,
        help=(
            f"input to executor. Can be a json string, json file, or S3 location. "
            "e.g. s3://bucket/key, /path/to/file.json, '{'foo': 'bar'}'"
        ),
    )
    parser.add_argument(
        "--output-location",
        "--response-location",
        "-o",
        dest="output_location",
        required=False,
        help=(f"optional response location to store response at. can be S3 or local file."),
    )
    return parser


def run_cli_executor(args: Optional[list[str]] = None):
    parsed_args = get_cli_parser().parse_args(args=args)

    executor_class = load_type_from_qualified_name(parsed_args.executor)

    if not issubclass(executor_class, BaseExecutor):
        raise ValueError(f"Executor class {executor_class} is not a subclass of BaseExecutor")

    executor_class.run_executor(parsed_args.request, parsed_args.output_location)


if __name__ == "__main__":  # pragma: no cover
    run_cli_executor()
