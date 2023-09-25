__all__ = [
    "b64_decoded_str",
    "b64_encoded_str",
    "generate_file_hash",
    "generate_path_hash",
    "sha256_hexdigest",
    "urlsafe_b64_decoded_str",
    "urlsafe_b64_encoded_str",
    "uuid_str",
]

import hashlib
import json
import logging
import re
import uuid
from base64 import standard_b64decode, standard_b64encode, urlsafe_b64decode, urlsafe_b64encode
from pathlib import Path
from typing import List, Optional, Union

from aibs_informatics_core.utils.json import JSON
from aibs_informatics_core.utils.os_operations import find_all_paths

logger = logging.getLogger(__name__)


def uuid_str(content: Optional[str] = None) -> str:
    """Get a UUID String, with option for using a seed to ensure determinism.

    Args:
        content (str, optional): A seed to use for determining UUID. Defaults to None.

    Returns:
        str: UUID appropriate string
    """
    if content is None:
        return str(uuid.uuid4())
    return str(uuid.uuid3(namespace=uuid.NAMESPACE_DNS, name=content))


def sha256_hexdigest(content: Optional[JSON] = None) -> str:
    """Create a SHA 256 Hex Digest string from optional content.

    If content is not provided, a unique Hex Digest is generated from UUID


    Args:
        content (JSON, optional): Input to base hexdigest off of. Defaults to None.

    Returns:
        str: a SHA 256 hex digest string.
    """
    if content is None:
        content = uuid_str()
    elif not isinstance(content, str):
        content = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def b64_decoded_str(encoded_str: str) -> str:
    """Decodes an encoded base64 string.

    Args:
        encoded_str (str): A string that has been previously encoded with base64

    Returns:
        str: a decoded base 64 string
    """
    try:
        return standard_b64decode(encoded_str.encode()).decode()
    except Exception as e:
        logger.error(e)
        logger.exception(e)
        raise e


def b64_encoded_str(decoded_str: str) -> str:
    """Encodes a string with base 64.

    Args:
        encoded_str (str): Any string

    Returns:
        str: an encoded base 64 string
    """
    return standard_b64encode(decoded_str.encode()).decode()


def urlsafe_b64_decoded_str(encoded_str: str) -> str:
    """Decodes an encoded base64 string.

    Args:
        encoded_str (str): A string that has been previously encoded with base64

    Returns:
        str: a decoded base 64 string
    """
    return urlsafe_b64decode(encoded_str.encode()).decode()


def urlsafe_b64_encoded_str(decoded_str: str) -> str:
    """Encodes a string with a URL SAFE version of base 64.

    Args:
        encoded_str (str): Any string

    Returns:
        str: an encoded base 64 string
    """
    return urlsafe_b64encode(decoded_str.encode()).decode()


def generate_path_hash(
    path: Union[str, Path],
    includes: Optional[List[str]] = None,
    excludes: Optional[List[str]] = None,
) -> str:
    """Generate a hash based on files found under a given path.

    Args:
        path (str): path to compute a hash
        includes (List[str], optional): list of regex patterns to include. Defaults to None.
        excludes (List[str], optional): list of regex patterns to exclude. Defaults to None.

    Returns:
        str: hash value
    """
    paths = find_all_paths(path, include_dirs=False)
    include_patterns = [re.compile(include) for include in includes or [r".*"]]
    exclude_patterns = [re.compile(exclude) for exclude in excludes or []]

    paths_to_hash = []
    for path in paths:
        # First check exclude patterns
        for exclude_pattern in exclude_patterns:
            if exclude_pattern.fullmatch(path):
                break
        else:
            # Now check include patterns
            for include_pattern in include_patterns:
                if include_pattern.fullmatch(path):
                    paths_to_hash.append(path)
                    break
    asset_hash = hashlib.sha256()
    for path in paths_to_hash:
        asset_hash.update(generate_file_hash(path).encode("utf-8"))

    return asset_hash.hexdigest()


def generate_file_hash(filename: Union[str, Path], bufsize: int = 128 * 1024) -> str:
    """

    https://stackoverflow.com/a/70215084/4544508

    Args:
        filename (str|Path): filepath to hash
        bufsize (int, optional): buffer size. Defaults to 128*1024.

    Returns:
        str: hash value of file
    """
    filename = str(filename)
    h = hashlib.sha256()
    buffer = bytearray(bufsize)
    buffer_view = memoryview(buffer)
    with open(filename, "rb", buffering=0) as f:
        while True:
            n = f.readinto(buffer_view)  # type: ignore
            if not n:
                break
            h.update(buffer_view[:n])
    return h.hexdigest()
