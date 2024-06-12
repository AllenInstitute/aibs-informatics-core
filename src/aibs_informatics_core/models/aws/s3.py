__all__ = [
    "S3PathStats",
    "S3Path",
    "S3URI",
    "S3BucketName",
    "S3KeyPrefix",
    "S3Key",
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
    Set,
    TypedDict,
    TypeVar,
    Union,
    overload,
)

if sys.version_info >= (3, 11):
    from typing import NotRequired


import marshmallow as mm
from dateutil import parser as date_parser  # type: ignore[import-untyped]
from marshmallow import validate as mm_validate

from aibs_informatics_core.collections import OrderedStrEnum, ValidatedStr
from aibs_informatics_core.models.base import CustomStringField, EnumField

if TYPE_CHECKING:  # pragma: no cover
    # from mypy_boto3_s3.service_resource import Object as S3_Object
    class S3_Object(Protocol):
        storage_class: Optional[str]

else:
    S3_Object = object


def validate_url(
    candidate_url: str,
    valid_url_schemes: Set[str] = {"http", "https", "ftp", "ftps", "file", "s3"},
    require_tld: bool = True,
    error_msg: str = "`{input}` is not a valid URL!",  # validate.URL will auto-interpolate {input}
):
    """Validate whether a string is a valid URL or not.

    Args:
        candidate_url (str): Candidate url string to validate
        valid_url_schemes (Set[str], optional): Which URL schemes to consider valid.
            Should be all lowercase. Defaults to {"http", "https", "ftp", "ftps", "file", "s3"}.
        require_tld (bool, optional): Whether the hostname needs to be a
            Fully Qualified Domain Name to pass validation. Defaults to True.
        error_msg (str, optional): Error message for if validation fails.
            Defaults to: "`{input}` is not a valid URL!"
    """
    validate = mm_validate.URL(schemes=valid_url_schemes, error=error_msg, require_tld=require_tld)
    validate(candidate_url)  # raises marshmallow.ValidationError if invalid


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


# https://stackoverflow.com/a/58248645/4544508
class S3BucketName(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(r"([A-Za-z0-9][A-Za-z0-9\-.]{1,61}[A-Za-z0-9])")

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
    regex_pattern: ClassVar[Pattern] = re.compile(r"[a-zA-Z0-9!_.*'()-]+(/[a-zA-Z0-9!_.*'()-]+)*")

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
class S3KeyPrefix(S3Key):
    regex_pattern: ClassVar[Pattern] = re.compile(r"[a-zA-Z0-9!_.*'()-]+(/[a-zA-Z0-9!_.*'()-]*)*")


_DOUBLE_SLASH_PATTERN = re.compile(r"([^:]/)(/)+")
_S3URI_PATTERN = re.compile(r"^s3:\/\/([^\/]+)\/?(.*)")


class S3Path(str):
    """An augmented `str` class intended to represent an aws internal `s3://` style URI.
    Has useful properties to get bucket, key, and a method to generate an S3 virtual-hosted-style
    URL if provided a region.

    For details on AWS S3 URL/URI formats see:
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-bucket-intro.html


    NOTE: `s3://` URI format looks like:
          s3://{bucket-name}/{key-name}

          The lowercase 's' in `s3://` is important, some services are case sensitive

    NOTE: S3 virtual-hosted-style URL format looks like:
          https://{bucket-name}.s3.{region}.amazonaws.com/{key-name}
    """

    def __new__(cls, *args, full_validate: bool = True, **kwargs):
        value = args[0]
        assert isinstance(value, str)
        value = cls.sanitize(value)
        cls.validate(value, full_validate=full_validate)
        return str.__new__(cls, *(value,), **kwargs)

    def __init__(self, *args, full_validate: bool = True, **kwargs):
        bucket, s3path = _S3URI_PATTERN.fullmatch(self).groups()  # type: ignore  # this will always match because validation happens in __new__
        self._bucket: str = bucket
        self._path: str = s3path
        self._full_validate = full_validate

    @classmethod
    def sanitize(cls, value: str) -> str:
        """
        Sanitize s3 uri inputs to make more compliant. Current steps:
            1. remove double slashes except after a colon
        """
        return _DOUBLE_SLASH_PATTERN.sub(r"\1", value)

    @classmethod
    def validate(cls, value: str, full_validate: bool):
        if not value.startswith("s3://"):
            raise mm.ValidationError(
                f"S3Path should start with 's3://' (case sensitive). "
                f"The provided tentative S3Path ({value}) does not!"
            )

        if full_validate:
            # `S3://` style URIs lack a Top Level Domain
            # So require_tld should be false for validation purposes
            escaped_self = value.replace("{", "{{").replace("}", "}}")
            validate_url(
                candidate_url=value,
                valid_url_schemes={"s3"},
                require_tld=False,
                error_msg=f"`{escaped_self} is not a valid internal style 's3://' URI!",
            )

    @classmethod
    def is_valid(cls, value: str, full_validate: bool = True) -> bool:
        try:
            cls.validate(value=value, full_validate=full_validate)
        except Exception:
            return False
        return True

    @classmethod
    def build(cls, bucket_name: str, key: str = "", full_validate: bool = True) -> "S3Path":
        """Build an `s3://` style URI given a bucket_name and key.

        There may be cases where the bucket_name or key is a placeholder
        (e.g. "${FILL_WITH_SOME_ENV_VAR}") in which case full validation can be
        skipped by setting full_validate=False
        """
        return cls(f"s3://{bucket_name}/{key.lstrip('/')}", full_validate=full_validate)

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def bucket_name(self) -> str:
        """Alias for bucket property"""
        return self.bucket

    @property
    def key(self) -> str:
        return self._path.lstrip("/")

    @property
    def key_with_folder_suffix(self) -> str:
        return str(Path(self.key)) + "/"

    @property
    def name(self) -> str:
        return Path(self.key).name if self.key else ""

    @property
    def parent(self) -> "S3Path":
        parent_key = "/".join(self.key.split("/")[:-1]).rstrip("/") + "/"
        return S3Path.build(bucket_name=self.bucket_name, key=parent_key)

    @property
    def with_folder_suffix(self) -> "S3Path":
        return S3Path.build(
            bucket_name=self.bucket_name,
            key=self.key_with_folder_suffix,
            full_validate=self._full_validate,
        )

    def has_folder_suffix(self) -> bool:
        return self.key.endswith("/")

    def as_dict(self) -> BucketAndKey:
        return BucketAndKey(Bucket=self.bucket, Key=self.key)

    def as_hosted_s3_url(self, aws_region: str) -> str:
        hosted_s3_url = f"https://{self.bucket}.s3.{aws_region}.amazonaws.com/{self.key}"
        return hosted_s3_url

    @classmethod
    def as_mm_field(cls) -> mm.fields.Field:
        return CustomStringField(S3Path)

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
        return S3Path(f"{self}{__other}", full_validate=self._full_validate)

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
        return S3Path(f"{self}/{__other}", full_validate=self._full_validate)

    def __rtruediv__(self, __other: Union[str, S3BucketName]) -> "S3Path":
        """Creates a new S3Path by constructing a str or S3Path key with this key

        Examples:
            >>> s3_uri = S3Path("s3://my-bucket/my-key") / "my-other-key"
            >>> assert s3_uri == "s3://my-bucket/my-other-key"

            >>> another_s3_uri = S3Path("s3://bucket1/key1") / S3Path("s3://bucket2/key2")
            >>> assert another_s3_uri == "s3://bucket1/key2"

        Args:
            __other (Union[str, S3Path]): The key to append to the end of this S3Path

        Returns:
            S3Path: a new S3Path with a new key
        """
        if S3Path.is_valid(__other):
            __other = S3Path(__other).bucket_name
        return S3Path.build(bucket_name=__other, key=self.key, full_validate=self._full_validate)

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
        return S3Path.build(
            bucket_name=self.bucket, key=__other, full_validate=self._full_validate
        )


S3URI = S3Path

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
