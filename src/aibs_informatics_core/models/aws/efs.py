import re
from functools import cached_property
from pathlib import Path
from typing import ClassVar, Optional, Union

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.aws.core import AWS_ACCOUNT_PATTERN_STR as AWS_ACCOUNT_PATTERN
from aibs_informatics_core.models.aws.core import AWS_REGION_PATTERN_STR as AWS_REGION_PATTERN
from aibs_informatics_core.models.aws.core import AWSRegion
from aibs_informatics_core.models.base import CustomStringField

FILE_SYSTEM_ID_PATTERN = r"fs-[0-9a-f]{8,40}"
ACCESS_POINT_ID_PATTERN = r"fsap-[0-9a-f]{8,40}"


class FileSystemId(ValidatedStr):
    # https://docs.aws.amazon.com/efs/latest/ug/API_CreateAccessPoint.html#efs-CreateAccessPoint-request-FileSystemId
    regex_pattern: ClassVar[re.Pattern] = re.compile(
        rf"(arn:(aws[-a-z]*):elasticfilesystem:({AWS_REGION_PATTERN})(?::{AWS_ACCOUNT_PATTERN}):file-system/)?({FILE_SYSTEM_ID_PATTERN})"
    )

    @property
    def normalized(self) -> "FileSystemId":
        return FileSystemId(self.resource_id)

    @property
    def resource_id(self) -> str:
        return self.get_match_groups()[-1]

    @property
    def region(self) -> Optional[str]:
        return self.get_match_groups()[-2]

    @property
    def arn_prefix(self) -> Optional[str]:
        return self.get_match_groups()[0]


class AccessPointId(ValidatedStr):
    # https://docs.aws.amazon.com/efs/latest/ug/API_CreateAccessPoint.html#efs-CreateAccessPoint-response-AccessPointId
    regex_pattern: ClassVar[re.Pattern] = re.compile(
        rf"(arn:(aws[-a-z]*):elasticfilesystem:({AWS_REGION_PATTERN})(?::{AWS_ACCOUNT_PATTERN}):access-point/)?({ACCESS_POINT_ID_PATTERN})"
    )

    @property
    def normalized(self) -> str:
        return self.resource_id

    @property
    def resource_id(self) -> str:
        return self.get_match_groups()[-1]

    @property
    def region(self) -> Optional[str]:
        return self.get_match_groups()[-2]

    @property
    def arn_prefix(self) -> Optional[str]:
        return self.get_match_groups()[0]


class FileSystemDNSName(ValidatedStr):
    # https://docs.aws.amazon.com/efs/latest/ug/mounting-fs.html
    regex_pattern: ClassVar[re.Pattern] = re.compile(
        rf"({FILE_SYSTEM_ID_PATTERN})\.efs\.({AWS_REGION_PATTERN})\.amazonaws\.com"
    )

    @property
    def file_system_id(self) -> FileSystemId:
        return FileSystemId(self.get_match_groups()[0])

    @property
    def region(self) -> AWSRegion:
        return AWSRegion(self.get_match_groups()[1])

    @classmethod
    def build(cls, file_system_id: str, region: str) -> "FileSystemDNSName":
        return cls(f"{file_system_id}.efs.{region}.amazonaws.com")


PATH_PATTERN = r".*"


class EFSPath(ValidatedStr):
    """
    Custom EFS File URI

    EFS Does not have a standard URI format. This class provides a custom URI format for EFS
    resources. The format is as follows:

    [efs://](<fs-dns-name>|<resource-id>)[:]/<path>

        Where:
        - <fs-dns-name> = <fs-id>.efs.<region>.amazonaws.com
        - <resource-id> = <fs-id> | <fsap-id>
        - <path> = path to file or directory
        - <region> = aws region

    Examples (using fs-12345678 as file system id):

        Using efs:// prefix...
        - efs://fs-12345678.efs.us-east-1.amazonaws.com:/my/file.txt    -> /my/file.txt
        - efs://fs-12345678.efs.us-east-1.amazonaws.com/my/file.txt     -> /my/file.txt
        - efs://fs-12345678:/my/file.txt                                -> /my/file.txt
        - efs://fs-12345678/my/file.txt                                 -> /my/file.txt
        - efs://fs-12345678                                             -> /
        - efs://fs-12345678:                                            -> /
        - efs://fs-12345678/                                            -> /
        - efs://fs-12345678:/                                           -> /

        Using no prefix...
        - fs-12345678.efs.us-east-1.amazonaws.com:/my/file.txt          -> /my/file.txt
        - fs-12345678:/my/file.txt                                      -> /my/file.txt
        - fs-12345678:/                                                 -> /
        - fs-12345678:                                                  -> /


    """

    regex_pattern: ClassVar[re.Pattern] = re.compile(
        # rf"""
        # (?:efs:\/\/(?!.*:\/)|(?:(?:efs:\/\/)?(?=.*:\/)))
        # (?:({FILE_SYSTEM_ID_PATTERN})\.efs\.{AWS_REGION_PATTERN}\.amazonaws\.com|({FILE_SYSTEM_ID_PATTERN}))
        # :?
        # ({PATH_PATTERN})
        # """
        rf"""
        (?:
            (?:efs://)(?:({FILE_SYSTEM_ID_PATTERN})\.efs\.{AWS_REGION_PATTERN}\.amazonaws\.com|({FILE_SYSTEM_ID_PATTERN})):?
        |
            (?:efs://)?(?:({FILE_SYSTEM_ID_PATTERN})\.efs\.{AWS_REGION_PATTERN}\.amazonaws\.com|({FILE_SYSTEM_ID_PATTERN})):
        )
        ({PATH_PATTERN})
        """,
        re.VERBOSE,
    )

    @property
    def root(self) -> Path:
        return Path("/")

    @property
    def raw_path(self) -> str:
        return self.get_match_groups()[-1]

    @property
    def path(self) -> Path:
        return self.root / self.raw_path

    @cached_property
    def file_system_id(self) -> FileSystemId:
        groups = self.get_match_groups()
        file_store_id_str = groups[0] or groups[1] or groups[2] or groups[3]
        return FileSystemId(file_store_id_str)

    def as_uri(self) -> str:
        return f"efs://{self.file_system_id}:{self.path}"

    def as_dns_uri(self, region: AWSRegion) -> str:
        return f"efs://{FileSystemDNSName.build(self.file_system_id, region)}:{self.path}"

    @classmethod
    def build(
        cls, resource_id: Union[FileSystemId, FileSystemDNSName, str], path: Union[Path, str]
    ) -> "EFSPath":
        file_system_id: FileSystemId
        if FileSystemId.is_valid(resource_id):
            file_system_id = FileSystemId(resource_id).normalized
        elif FileSystemDNSName.is_valid(resource_id):
            file_system_id = FileSystemDNSName(resource_id).file_system_id
        else:
            raise ValueError(
                f"Invalid resource_id: {resource_id}. does not match file system id or dns name"
            )
        path = Path("/") / path
        return cls(f"{file_system_id}:{path.as_posix()}")

    @classmethod
    def as_mm_field(cls) -> CustomStringField:
        return CustomStringField(cls)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, str) and EFSPath.is_valid(__value):
            return self.as_uri() == EFSPath(__value).as_uri()
        return super().__eq__(__value)

    def __truediv__(self, __other: Union[str, Path, "EFSPath"]) -> "EFSPath":
        """Appends a string or EFSPath key to the end of this EFSPath using the `/` operator

        Examples:
            >>> efs_uri = EFSPath("efs://fs-11111111/my-key") / "my-other-key"
            >>> assert efs_uri == "efs://fs-11111111/my-key/my-other-key"

            >>> another_efs_uri = EFSPath("efs://fs-11111111/key1") / EFSPath("efs://fs-22222222/key2")
            >>> assert another_efs_uri == "efs://fs-11111111/key1/key2"

        Args:
            __other (Union[str, EFSPath]): The key to append to the end of this EFSPath

        Returns:
            EFSPath: a new EFSPath with the appended key using the `/` operator
        """
        if isinstance(__other, EFSPath):
            __other = __other.path
        elif isinstance(__other, str):
            __other = Path(__other)

        if __other.is_relative_to("/"):
            __other = __other.relative_to("/")
        return EFSPath.build(resource_id=self.file_system_id, path=self.path / __other)

    def __rtruediv__(self, __other: str) -> "EFSPath":
        """Creates a new EFSPath by constructing a str or EFSPath key with this key

        Examples:
            >>> efs_uri = EFSPath("efs://fs-12345678/my-key") / "my-other-key"
            >>> assert efs_uri == "efs://fs-11111111/my-other-key"

            >>> another_efs_uri = EFSPath("efs://fs-11111111/key1") / EFSPath("fs-22222222/key2")
            >>> assert another_efs_uri == "efs://fs-11111111/key2"

        Args:
            __other (Union[str, EFSPath]): The key to append to the end of this EFSPath

        Returns:
            EFSPath: a new EFSPath with a new key
        """
        if EFSPath.is_valid(__other):
            return EFSPath(__other) / self
        elif FileSystemId.is_valid(__other):
            return EFSPath.build(FileSystemId(__other).normalized, path=self.path)
        elif FileSystemDNSName.is_valid(__other):
            return EFSPath.build(FileSystemDNSName(__other).file_system_id, path=self.path)
        else:
            return EFSPath.build(
                self.file_system_id, path=Path(__other) / self.path.relative_to("/")
            )

    def __floordiv__(self, __other: Union[str, Path, "EFSPath"]) -> "EFSPath":
        """Creates a new EFSPath by constructing a str or EFSPath file path with this fs id

        Examples:
            >>> efs_uri = EFSPath("efs://fs-11111111/my-key") // "my-other-key"
            >>> assert efs_uri == "efs://fs-11111111/my-other-key"

            >>> another_efs_uri = EFSPath("efs://fs-11111111/key1") // EFSPath("efs://fs-22222222/key2")
            >>> assert another_efs_uri == "efs://fs-11111111/key2"

        Args:
            __other (Union[str, EFSPath]): The key to append to the end of this EFSPath

        Returns:
            EFSPath: a new EFSPath with a new key
        """
        if isinstance(__other, EFSPath):
            __other = __other.path
        return EFSPath.build(resource_id=self.file_system_id, path=__other)
