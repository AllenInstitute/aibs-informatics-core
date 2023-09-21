__all__ = [
    "uuid_str",
    "sha256_hexdigest",
    "b64_decoded_str",
    "b64_encoded_str",
    "urlsafe_b64_decoded_str",
    "urlsafe_b64_encoded_str",
]

import hashlib
import json
import logging
import uuid
from base64 import standard_b64decode, standard_b64encode, urlsafe_b64decode, urlsafe_b64encode
from typing import Optional

from aibs_informatics_core.utils.json import JSON

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
