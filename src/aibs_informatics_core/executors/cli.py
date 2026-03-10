import logging

from aibs_informatics_core.executors.base import BaseExecutor
from aibs_informatics_core.utils.modules import load_type_from_qualified_name

logger = logging.getLogger(__name__)


def get_cli_parser():
    """Build an argument parser for the executor CLI.

    Returns:
        An ``argparse.ArgumentParser`` configured with ``--executor``,
        ``--input``, and ``--output-location`` arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Executor CLI")

    parser.add_argument(
        "--executor",
        dest="executor",
        required=True,
        help=(
            "executor class to run. Must be a fully qualified name of the executor class. "
            "e.g. aibs_informatics_aws_lambda.common.executor.BaseExecutor"
        ),
    )
    parser.add_argument(
        "--input",
        "--request",
        "-i",
        dest="request",
        required=True,
        help=(
            "input to executor. Can be a json string, json file, or S3 location. "
            "e.g. s3://bucket/key, /path/to/file.json, '{'foo': 'bar'}'"
        ),
    )
    parser.add_argument(
        "--output-location",
        "--response-location",
        "-o",
        dest="output_location",
        required=False,
        help=("optional response location to store response at. can be S3 or local file."),
    )
    return parser


def run_cli_executor(args: list[str] | None = None):
    """Run an executor from the command line.

    Parses CLI arguments to load an executor class and execute it with the
    provided input. Optionally writes the response to an output location.

    Args:
        args: Optional list of CLI arguments. If None, reads from ``sys.argv``.

    Raises:
        ValueError: If the specified executor class is not a subclass of ``BaseExecutor``.
    """
    parsed_args = get_cli_parser().parse_args(args=args)

    executor_class = load_type_from_qualified_name(parsed_args.executor)

    if not issubclass(executor_class, BaseExecutor):
        raise ValueError(f"Executor class {executor_class} is not a subclass of BaseExecutor")

    executor_class.run_executor(parsed_args.request, parsed_args.output_location)


if __name__ == "__main__":  # pragma: no cover
    run_cli_executor()
