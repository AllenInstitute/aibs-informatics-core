__all__ = [
    "S3PathStats",
    "S3Path",
    "S3PathPlaceholder",
    "S3URI",
    "S3BucketName",
    "S3BucketNamePlaceholder",
    "S3KeyPrefix",
    "S3Key",
    "S3KeyPlaceholder",
    "S3StorageClass",
    "S3StorageClassStr",
    "S3TransferRequest",
    "S3CopyRequest",
    "S3TransferResponse",
    "S3CopyResponse",
    "S3UploadRequest",
    "S3DownloadRequest",
    "S3UploadResponse",
    "S3RestoreStatus",
    "S3RestoreStatusEnum",
]

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Pattern,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)
from urllib.parse import quote

from aibs_informatics_core.exceptions import ValidationError

if sys.version_info >= (3, 11):
    from typing import NotRequired

import marshmallow as mm
from dateutil import parser as date_parser  # type: ignore[import-untyped]

from aibs_informatics_core.collections import OrderedStrEnum, ValidatedStr
from aibs_informatics_core.models.base import CustomStringField, EnumField

if TYPE_CHECKING:  # pragma: no cover
    # from mypy_boto3_s3.service_resource import Object as S3_Object
    class S3_Object(Protocol):
        storage_class: Optional[str]

else:
    S3_Object = object


if sys.version_info >= (3, 11):

    class BucketAndKey(TypedDict):
        Bucket: str
        Key: str
        VersionId: NotRequired[str]

else:  # pragma: no cover

    class _BucketAndKeyOpt(TypedDict, total=False):
        VersionId: str

    class _BucketAndKeyReq(TypedDict):
        Bucket: str
        Key: str

    class BucketAndKey(_BucketAndKeyReq, _BucketAndKeyOpt):
        pass


@dataclass
class S3PathStats:
    last_modified: datetime
    size_bytes: int
    object_count: Optional[int]

    def __getitem__(self, key):
        return super().__getattribute__(key)


# --- Placeholder (tight & brace-safe; adjust char class as you like) ---
PLACEHOLDER_PATTERN = r"(?:\$\{[A-Za-z0-9._\-\[\]]+\})"

NORMAL_CHARS = r"a-zA-Z0-9!_.*'()\-"
SPECIAL_CHARS = r"&$@=;:+,? "

# S3 Key Pattern Pattern: strictly no placeholders
# NOTE: S3 keys can be empty strings, so we allow that here
S3_KEY_PATTERN_STR_NO_VARS = rf"(?:[{NORMAL_CHARS}{SPECIAL_CHARS}]+/?)*"

KEY_RUN = rf"[{NORMAL_CHARS}{SPECIAL_CHARS}]+"  # non-slash run
KEY_TOKEN = rf"(?:{KEY_RUN}|{PLACEHOLDER_PATTERN})"  # run OR placeholder
KEY_SEG = rf"{KEY_TOKEN}+"  # one or more tokens per segment

# Mixed tokens where segments are separated by slashes, and can be empty (for trailing slash)
S3_KEY_PATTERN_STR_VARS = rf"(?:/(?={KEY_SEG}))?{KEY_SEG}(?:/{KEY_SEG})*/?|/?"

# S3 Bucket Name Pattern

BUCKET_RUN = r"[A-Za-z0-9.-]+"  # no slash
BUCKET_TOKEN = rf"(?:{BUCKET_RUN}|{PLACEHOLDER_PATTERN})"

# Strict bucket pattern
S3_BUCKET_NAME_PATTERN_STR_NO_VARS = r"(?:[A-Za-z0-9][A-Za-z0-9\-.]{1,61}[A-Za-z0-9])"

# Mixed tokens where the ends are alnum OR placeholder; handles 'bucket-${x}', '${x}-bucket', etc.
S3_BUCKET_NAME_PATTERN_MIXED = (
    rf"(?:"
    rf"(?:[A-Za-z0-9]|{PLACEHOLDER_PATTERN})"
    rf"(?:{BUCKET_TOKEN})*"
    rf"(?:[A-Za-z0-9]|{PLACEHOLDER_PATTERN})"
    rf")"
)

# Full bucket pattern: plain literal OR mixed OR single placeholder
S3_BUCKET_NAME_PATTERN_STR_VARS = (
    rf"(?:{S3_BUCKET_NAME_PATTERN_STR_NO_VARS}|"
    rf"{S3_BUCKET_NAME_PATTERN_MIXED}|"
    rf"{PLACEHOLDER_PATTERN})"
)


# https://stackoverflow.com/a/58248645/4544508
class S3BucketName(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(S3_BUCKET_NAME_PATTERN_STR_NO_VARS)

    def __truediv__(self, __other: str) -> "S3Path":
        """Creates a S3Path

        Examples:
            >>> s3_uri = S3BucketName("my-bucket") / "my-key"
            >>> assert s3_uri == "s3://my-bucket/my-key"

            >>> another_s3_uri = S3BucketName("bucket1") / S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key2"

        Args:
            __other (Union[str, S3Path]): The key or key of path to use for the S3Path

        Returns:
            S3Path: a new S3Path with the appended key using the `/` operator
        """

        if S3Path.is_valid(__other):
            __other = S3Path(__other).key
        return S3Path.build(bucket_name=self, key=__other)


class S3Key(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(S3_KEY_PATTERN_STR_VARS)

    @property
    def components(self) -> List[str]:
        return self.split("/")

    def __rtruediv__(self, __other: str) -> "S3Key":
        """Creates a new S3 Key

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with a new key
        """
        if isinstance(__other, str):
            prefix = __other.rstrip("/")
            return S3Key((prefix + "/" if prefix else "") + self)
        raise TypeError(f"{type(__other)} not supported for / operations with {type(self)}")


# https://stackoverflow.com/questions/58712045/regular-expression-for-amazon-s3-object-name
# NOTE: For now, this is is the same as S3Key. We made S3Key regex support an empty string
#       which was the only difference between the two.
class S3KeyPrefix(S3Key):
    pass


_DOUBLE_SLASH_PATTERN = re.compile(r"([^:]/)(/)+")


class S3Path(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(
        rf"^s3:\/\/({S3_BUCKET_NAME_PATTERN_STR_NO_VARS})(?:\/({S3_KEY_PATTERN_STR_NO_VARS}))?"
    )

    @classmethod
    def _sanitize(cls, value: str, *args, **kwargs) -> str:
        value = str(value)
        value = value[:3] + _DOUBLE_SLASH_PATTERN.sub(r"\1", value[3:])
        return value

    @cached_property
    def bucket(self) -> S3BucketName:
        return S3BucketName(self.get_match_groups()[0])

    @property
    def bucket_name(self) -> str:
        """Alias for bucket property"""
        return self.bucket

    @cached_property
    def key(self) -> S3Key:
        if key := self.get_match_groups()[1]:
            return S3Key(key)
        return S3Key("")

    @property
    def key_with_folder_suffix(self) -> str:
        return str(Path(self.key)) + "/"

    @property
    def name(self) -> str:
        return Path(self.key).name if self.key else ""

    @property
    def parent(self) -> "S3Path":
        # Handle root-level (just the bucket)
        if not self.key or self.key == "/":
            return S3Path.build(bucket_name=self.bucket_name, key="")

        # Strip trailing slash before splitting
        parent_key = "/".join(self.key.rstrip("/").split("/")[:-1]).rstrip("/") + "/"
        return S3Path.build(bucket_name=self.bucket_name, key=parent_key)

    @property
    def with_folder_suffix(self) -> "S3Path":
        return S3Path.build(bucket_name=self.bucket_name, key=self.key_with_folder_suffix)

    def has_folder_suffix(self) -> bool:
        return self.key.endswith("/")

    def as_dict(self) -> BucketAndKey:
        return BucketAndKey(Bucket=self.bucket, Key=self.key)

    def as_hosted_s3_url(self, aws_region: str) -> str:
        # TODO: need to encode special characters in key
        encoded_key = quote(self.key, safe="/")
        hosted_s3_url = f"https://{self.bucket}.s3.{aws_region}.amazonaws.com/{encoded_key}"
        return hosted_s3_url

    @classmethod
    def as_mm_field(cls) -> mm.fields.Field:
        return CustomStringField(S3Path)

    @classmethod
    def build(cls, bucket_name: str, key: str = "", **kwargs) -> "S3Path":
        """Build an `s3://` style URI given a bucket_name and key.

        There may be cases where the bucket_name or key is a placeholder
        (e.g. "${FILL_WITH_SOME_ENV_VAR}") in which case you must set allow_placeholders=True
        """
        bucket = S3BucketName(bucket_name, **kwargs)
        key = S3Key(key, **kwargs)
        return cls(f"s3://{bucket}/{key}", **kwargs)

    def __add__(self, __other: Union[str, "S3Path"]) -> "S3Path":
        """Appends a string or S3Path key to the end of this S3Path

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") + "-my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-key-my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") + S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key1key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with the appended key
        """
        if isinstance(__other, S3Path):
            __other = __other.key
        return S3Path(f"{self}{__other}")

    def __truediv__(self, __other: Union[str, "S3Path"]) -> "S3Path":
        """Appends a string or S3Path key to the end of this S3Path using the `/` operator

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") / "my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-key/my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") / S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key1/key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with the appended key using the `/` operator
        """
        if isinstance(__other, S3Path):
            __other = __other.key
        return S3Path(f"{self}/{__other}")

    def __floordiv__(self, __other: Union[str, "S3Path"]) -> "S3Path":
        """Creates a new S3Path by constructing a str or S3Path key with this bucket

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") // "my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") // S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with a new key
        """
        if isinstance(__other, S3Path):
            __other = __other.key
        return S3Path.build(bucket_name=self.bucket, key=__other)


# Ensure backwards compatibility with old S3URI class name
S3URI = S3Path


class ConditionalPlaceholderStr(ValidatedStr):
    _placeholder_pattern: ClassVar[Pattern] = re.compile(PLACEHOLDER_PATTERN)

    def __new__(cls, value, *args, allow_placeholders: bool = False, **kwargs):
        return super().__new__(cls, value, *args, **kwargs)

    def __init__(self, *args, allow_placeholders: bool = False, **kwargs):
        self._allow_placeholders = allow_placeholders
        # TODO: This is to ensure backwards compatibility with the old `full_validate` kwarg
        #       Please remove this in the next major release
        if "full_validate" in kwargs:
            self._allow_placeholders = not kwargs.pop("full_validate")

    def _validate(self):
        super()._validate()
        if not self.allow_placeholders:
            if self.has_placeholder:
                raise ValidationError(
                    f"Placeholders are not allowed in {self} ({type(self)})"
                    f"with allow_placeholders={self.allow_placeholders}"
                )

    @property
    def allow_placeholders(self) -> bool:
        return self._allow_placeholders

    @cached_property
    def has_placeholder(self) -> bool:
        return bool(self._placeholder_pattern.search(self))


# https://stackoverflow.com/a/58248645/4544508
class S3BucketNamePlaceholder(ConditionalPlaceholderStr):
    regex_pattern: ClassVar[Pattern] = re.compile(S3_BUCKET_NAME_PATTERN_STR_VARS)

    def __truediv__(self, __other: str) -> "S3PathPlaceholder":
        """Creates a S3PathProxy

        Examples:
            >>> s3_uri = S3BucketName("my-bucket") / "my-key"
            >>> assert s3_uri == "s3://my-bucket/my-key"

            >>> another_s3_uri = S3BucketName("bucket1") / S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key2"

        Args:
            __other (Union[str, S3Path]): The key or key of path to use for the S3Path

        Returns:
            S3Path: a new S3Path with the appended key using the `/` operator
        """

        if S3PathPlaceholder.is_valid(__other):
            __other = S3PathPlaceholder(__other).key
        return S3PathPlaceholder.build(bucket_name=self, key=__other)


class S3KeyPlaceholder(ConditionalPlaceholderStr):
    regex_pattern: ClassVar[Pattern] = re.compile(S3_KEY_PATTERN_STR_VARS)

    @property
    def components(self) -> List[str]:
        return self.split("/")

    def __rtruediv__(self, __other: str) -> "S3KeyPlaceholder":
        """Creates a new S3 Key

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with a new key
        """
        if isinstance(__other, str):
            prefix = __other.rstrip("/")
            return S3KeyPlaceholder((prefix + "/" if prefix else "") + self)
        raise TypeError(f"{type(__other)} not supported for / operations with {type(self)}")


class S3PathPlaceholder(ConditionalPlaceholderStr):
    regex_pattern: ClassVar[Pattern] = re.compile(
        rf"^s3:\/\/({S3_BUCKET_NAME_PATTERN_STR_VARS})(?:\/({S3_KEY_PATTERN_STR_VARS}))?"
    )

    @classmethod
    def _sanitize(cls, value: str, *args, **kwargs) -> str:
        value = value[:3] + _DOUBLE_SLASH_PATTERN.sub(r"\1", value[3:])
        return value

    @cached_property
    def bucket(self) -> S3BucketNamePlaceholder:
        return S3BucketNamePlaceholder(
            self.get_match_groups()[0], allow_placeholders=self.allow_placeholders
        )

    @property
    def bucket_name(self) -> str:
        """Alias for bucket property"""
        return self.bucket

    @cached_property
    def key(self) -> S3KeyPlaceholder:
        if key := self.get_match_groups()[1]:
            return S3KeyPlaceholder(key, allow_placeholders=self.allow_placeholders)
        return S3KeyPlaceholder("")

    @property
    def key_with_folder_suffix(self) -> str:
        return str(Path(self.key)) + "/"

    @property
    def name(self) -> str:
        return Path(self.key).name if self.key else ""

    @property
    def parent(self) -> "S3PathPlaceholder":
        parent_key = "/".join(self.key.rstrip("/").split("/")[:-1]).rstrip("/") + "/"
        return S3PathPlaceholder.build(
            bucket_name=self.bucket_name,
            key=parent_key,
            allow_placeholders=self.allow_placeholders,
        )

    @property
    def with_folder_suffix(self) -> "S3PathPlaceholder":
        return S3PathPlaceholder.build(
            bucket_name=self.bucket_name,
            key=self.key_with_folder_suffix,
            allow_placeholders=self.allow_placeholders,
        )

    def has_folder_suffix(self) -> bool:
        return self.key.endswith("/")

    def as_dict(self) -> BucketAndKey:
        return BucketAndKey(Bucket=self.bucket, Key=self.key)

    def as_hosted_s3_url(self, aws_region: str) -> str:
        # TODO: need to encode special characters in key
        encoded_key = quote(self.key, safe="/")
        hosted_s3_url = f"https://{self.bucket}.s3.{aws_region}.amazonaws.com/{encoded_key}"
        return hosted_s3_url

    @classmethod
    def as_mm_field(cls) -> mm.fields.Field:
        return CustomStringField(S3PathPlaceholder)

    @classmethod
    def build(
        cls, bucket_name: str, key: str = "", allow_placeholders: bool = False, **kwargs
    ) -> "S3PathPlaceholder":
        """Build an `s3://` style URI given a bucket_name and key.

        There may be cases where the bucket_name or key is a placeholder
        (e.g. "${FILL_WITH_SOME_ENV_VAR}") in which case you must set allow_placeholders=True
        """
        bucket = S3BucketNamePlaceholder(
            bucket_name, allow_placeholders=allow_placeholders, **kwargs
        )
        key = S3KeyPlaceholder(key, allow_placeholders=allow_placeholders, **kwargs)
        return cls(f"s3://{bucket}/{key}", allow_placeholders=allow_placeholders, **kwargs)

    def __add__(self, __other: Union[str, "S3PathPlaceholder", S3Path]) -> "S3PathPlaceholder":
        """Appends a string or S3Path key to the end of this S3Path

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") + "-my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-key-my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") + S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key1key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with the appended key
        """
        if isinstance(__other, (S3PathPlaceholder, S3Path)):
            __other = __other.key
        return S3PathPlaceholder(f"{self}{__other}", allow_placeholders=self.allow_placeholders)

    def __truediv__(self, __other: Union[str, S3Path, "S3PathPlaceholder"]) -> "S3PathPlaceholder":
        """Appends a string or S3Path key to the end of this S3Path using the `/` operator

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") / "my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-key/my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") / S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key1/key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with the appended key using the `/` operator
        """
        if isinstance(__other, (S3Path, S3PathPlaceholder)):
            __other = __other.key
        return S3PathPlaceholder(f"{self}/{__other}", allow_placeholders=self.allow_placeholders)

    def __floordiv__(
        self, __other: Union[str, S3Path, "S3PathPlaceholder"]
    ) -> "S3PathPlaceholder":
        """Creates a new S3Path by constructing a str or S3Path key with this bucket

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") // "my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") // S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with a new key
        """
        if isinstance(__other, (S3Path, S3PathPlaceholder)):
            __other = __other.key
        return S3PathPlaceholder.build(
            bucket_name=self.bucket, key=__other, allow_placeholders=self.allow_placeholders
        )


T = TypeVar("T", S3Path, Path)
U = TypeVar("U", S3Path, Path)


@dataclass
class S3TransferRequest(Generic[T, U]):
    source_path: T
    destination_path: U


@dataclass
# class S3CopyRequest:
class S3CopyRequest(S3TransferRequest[S3Path, S3Path]):
    extra_args: Optional[Dict[str, Any]] = None


@dataclass
class S3TransferResponse:
    request: S3TransferRequest
    failed: bool = False
    reason: Optional[str] = None

    def __post_init__(self):
        if self.failed and not self.reason:
            raise ValueError(f"{self} must have a reason if failed.")


@dataclass
class S3CopyResponse:
    request: S3CopyRequest
    failed: bool = False
    reason: Optional[str] = None

    def __post_init__(self):
        if self.failed and not self.reason:
            raise ValueError(f"{self} must have a reason if failed.")


@dataclass
class S3UploadRequest(S3TransferRequest[Path, S3Path]):
    extra_args: Optional[Dict[str, Any]] = None


@dataclass
class S3DownloadRequest(S3TransferRequest[S3Path, Path]):
    pass


@dataclass
class S3UploadResponse:
    request: S3UploadRequest
    failed: bool = False
    reason: Optional[str] = None

    def __post_init__(self):
        if self.failed and not self.reason:
            raise ValueError(f"{self} must have a reason if failed.")


class S3RestoreStatusEnum(OrderedStrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


@dataclass
class S3RestoreStatus:
    restore_status: S3RestoreStatusEnum
    restore_expiration_time: Optional[datetime] = None

    @classmethod
    def from_raw_s3_restore_status(cls, raw_s3_restore_status: Optional[str]) -> "S3RestoreStatus":
        if raw_s3_restore_status is None:
            # Example of what boto3 s3.Object.restore property returns:
            # None
            return cls(restore_status=S3RestoreStatusEnum.NOT_STARTED)
        elif 'ongoing-request="true"' == raw_s3_restore_status:
            # Example of what boto3 s3.Object.restore property returns:
            # 'ongoing-request="true"'
            return cls(restore_status=S3RestoreStatusEnum.IN_PROGRESS)
        elif 'ongoing-request="false"' in raw_s3_restore_status:
            # Examples of what boto3 s3.Object.restore property returns:
            # 'ongoing-request="false", expiry-date="Fri, 21 Dec 2012 00:00:00 GMT"'
            # 'ongoing-request="false", expiry-date="Fri, 31 Mar 2023 00:00:00 GMT"'
            raw_time_str = raw_s3_restore_status.split("expiry-date=")[-1].strip('"')
            parsed_time = date_parser.parse(raw_time_str)
            return cls(
                restore_status=S3RestoreStatusEnum.FINISHED,
                restore_expiration_time=parsed_time,
            )
        else:
            raise RuntimeError(
                f"Could not parse the following raw_s3_restore_status: {raw_s3_restore_status}"
            )


class S3StorageClass(OrderedStrEnum):
    """OrderedStrEnum describing s3 storage classes from most to least accessible

    Convention: Deeper, less accessible storage classes are considered ">" than shallow, more
                accessible classes. (e.g. DEEP_ARCHIVE > STANDARD, GLACIER > GLACIER_IR, ...)
    """

    # Ordered from most accessible to least accessible
    # See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html
    STANDARD = "STANDARD"
    STANDARD_IA = "STANDARD_IA"
    INTELLIGENT_TIERING = "INTELLIGENT_TIERING"
    ONEZONE_IA = "ONEZONE_IA"
    GLACIER_IR = "GLACIER_IR"
    GLACIER = "GLACIER"
    DEEP_ARCHIVE = "DEEP_ARCHIVE"
    # The following are special in that it's not easy to transition to or from them:
    OUTPOSTS = "OUTPOSTS"
    REDUCED_REDUNDANCY = "REDUCED_REDUNDANCY"

    @classmethod
    def from_boto_s3_obj(cls, s3_obj: S3_Object) -> "S3StorageClass":
        """Get S3StorageClass of an Boto3 S3_Object returned by s3.get_object"""
        if s3_obj.storage_class is None:
            return S3StorageClass.STANDARD
        else:
            return S3StorageClass(s3_obj.storage_class)

    @classmethod
    def list_archive_storage_classes(cls) -> List["S3StorageClass"]:
        """Storage classes that require a 'restore' operation to interact with the s3 object"""
        return [cls("GLACIER"), cls("DEEP_ARCHIVE")]

    @classmethod
    def list_transitionable_storage_classes(cls) -> List["S3StorageClass"]:
        return [
            cls("STANDARD"),
            cls("STANDARD_IA"),
            cls("INTELLIGENT_TIERING"),
            cls("ONEZONE_IA"),
            cls("GLACIER_IR"),
            cls("GLACIER"),
            cls("DEEP_ARCHIVE"),
        ]

    @classmethod
    def as_mm_field(cls) -> mm.fields.Field:
        return EnumField(S3StorageClass)


S3StorageClassStr = Literal[
    "STANDARD",
    "STANDARD_IA",
    "INTELLIGENT_TIERING",
    "ONEZONE_IA",
    "GLACIER_IR",
    "GLACIER",
    "DEEP_ARCHIVE",
    "OUTPOSTS",
    "REDUCED_REDUNDANCY",
]
