__all__ = [
    "ArchiveType",
    "extract_archive",
    "make_archive",
    "move_path",
    "copy_path",
    "remove_path",
    "get_path_size_bytes",
    "get_path_hash",
    "find_paths",
    "get_path_with_root",
    "strip_path_root",
    "PathLock",
    "CannotAcquirePathLockError",
]

import errno
import fcntl
import hashlib
import logging
import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Pattern, Sequence, Union, cast

from aibs_informatics_core.utils.os_operations import find_all_paths

ArchiveFile = Union[tarfile.TarFile, zipfile.ZipFile]


logger = logging.getLogger(__name__)


ArchiveFormat = Literal[
    "tar",
    "bztar",
    "gztar",
    "xztar",
    "zip",
]


class ArchiveType(Enum):
    # https://docs.python.org/3/library/shutil.html#shutil.get_archive_formats
    TAR = "tar"
    TAR_BZ = "bztar"
    TAR_GZ = "gztar"
    TAR_XZ = "xztar"
    ZIP = "zip"

    @property
    def archive_format(self) -> ArchiveFormat:
        return cast(ArchiveFormat, self.value)

    def is_archive_type(self, path: Path) -> bool:
        try:
            return self == self.from_path(path)
        except:
            return False

    @classmethod
    def is_archive(cls, path: Path) -> bool:
        try:
            cls.from_path(path)
        except:
            return False
        else:
            return True

    @classmethod
    def from_path(cls, path: Path) -> "ArchiveType":
        if not path.exists() or path.is_dir():
            raise ValueError(f"Path {path} does not exist or is a directory")
        if tarfile.is_tarfile(path):
            compression_type = cls._get_compression_type(path)
            if compression_type == "gz":
                return ArchiveType.TAR_GZ
            elif compression_type == "bz":
                return ArchiveType.TAR_BZ
            elif compression_type == "xz":
                return ArchiveType.TAR_XZ
            else:
                return ArchiveType.TAR
        elif zipfile.is_zipfile(path):
            return ArchiveType.ZIP
        else:
            raise ValueError(f"Cannot infer type")

    @classmethod
    def _get_compression_type(cls, path: Path) -> Optional[Literal["gz", "bz", "xz", "zip"]]:
        file_sign_mapping: Dict[bytes, Literal["gz", "bz", "xz", "zip"]] = {
            b"\x1f\x8b\x08": "gz",
            b"\x42\x5a\x68": "bz",
            b"\xfd\x37\x7a\x58\x5a\x00": "xz",
            b"\x50\x4b\x03\x04": "zip",
        }

        max_len = max(len(x) for x in file_sign_mapping)
        with open(path, "rb") as f:
            file_start = f.read(max_len)
        for file_sign, filetype in file_sign_mapping.items():
            if file_start.startswith(file_sign):
                return filetype
        return None


def extract_archive(source_path: Path, destination_path: Optional[Path] = None) -> Path:
    """Untar/unzip data batch into a dedicate folder
    Example: batch_of_samples.tar.gz -> batch_of_samples

    Args:
        source_path (Path): archived batch data
        destination_path (Optional[Path]): Optional destination path for extracted data.
            If none, then source path name used with extension removed.

    Raises:
        RuntimeError: If extraction fails

    Returns:
        Path: path to the untarred data
    """
    archive_type = ArchiveType.from_path(source_path)

    extracted_path = destination_path or Path(tempfile.mkdtemp())

    shutil.unpack_archive(
        filename=str(source_path),
        extract_dir=str(extracted_path),
        format=archive_type.archive_format,
    )
    return extracted_path


def make_archive(
    source_path: Path,
    destination_path: Optional[Path] = None,
    archive_type: Union[ArchiveType, ArchiveFormat] = ArchiveType.TAR_GZ,
) -> Path:
    """tar/zip data batch from a folder
    Example: batch_of_samples -> batch_of_samples.tar.gz

    Args:
        source_path (Path): folder of data to archive
        destination_path (Optional[Path]): Optional destination path for archived file.
            If none, then tmp file is created and used

    Raises:
        RuntimeError: If archiving operation fails

    Returns:
        Path: path to the untarred data
    """

    archive_path = destination_path or Path(tempfile.mktemp())
    if not isinstance(archive_type, ArchiveType):
        archive_type = ArchiveType(archive_type)

    try:
        actual_archive_path = Path(
            shutil.make_archive(
                base_name=str(archive_path.with_suffix("")),
                root_dir=str(source_path),
                base_dir=None,
                format=archive_type.archive_format,
            )
        )

        # shutil.make_archive takes base name and appends the appropriate suffix.
        # This means we can't say "write at X". We must move results, but only if different.
        if actual_archive_path != archive_path:
            move_path(actual_archive_path, archive_path)
        return archive_path
    except Exception as e:
        raise ValueError(f"Error extracting file {source_path}. [{e}]") from e


def find_filesystem_boundary(starting_path: Path) -> Path:
    """Given some starting Path, determine the nearest filesystem boundary (mount point).
    If no mount is found, then this function will return the first parent directory PRIOR
    to the filesystem anchor.

    >>> find_filesystem_boundary(Path("/allen/scratch/aibstemp"))
    PosixPath('/allen/scratch')

    >>> find_filesystem_boundary(Path("/tmp/random_file.txt"))
    PosixPath('/tmp')

    Args:
        starting_path (Path): The starting Path

    Raises:
        RuntimeError: If the provided starting_path cannot resolve to a real existing path

    Returns:
        Path: The path of the nearest filesystem boundary OR the first parent directory prior
            to the filesystem anchor (example anchors: "/", "c:\\")
    """
    current_path = starting_path.resolve()
    while current_path.parent != Path(current_path.anchor):
        if current_path.is_mount():
            break
        current_path = current_path.parent

    if current_path.exists():
        return current_path
    else:
        raise OSError(f"Could not find a real filesystem boundary for: {str(starting_path)}")


def move_path(source_path: Path, destination_path: Path, exists_ok: bool = False):
    """Alias to simple mv command from one path to another

    Args:
        source_path (Path): source path
        destination_path (Path): destination path
        exists_ok (bool, optional): if true, overwrites destination. Defaults to False.

    """
    if destination_path.exists():
        if not exists_ok:
            raise ValueError(f"Cannot move path to {destination_path}. destination exists!")
        remove_path(destination_path)

    shutil.move(str(source_path), destination_path)


def copy_path(source_path: Path, destination_path: Path, exists_ok: bool = False):
    """Copies path from source to destination

    Args:
        source_path (Path): source path
        destination_path (Path): destination path
        exists_ok (bool, optional): if true, overwrites destination. Defaults to False.

    """
    if source_path.is_file():
        if destination_path.exists():
            if not exists_ok:
                raise ValueError(f"Cannot copy path to {destination_path}. destination exists!")
            remove_path(destination_path)
        shutil.copy(source_path, destination_path)
    else:
        shutil.copytree(source_path, destination_path, dirs_exist_ok=exists_ok)


def remove_path(path: Path):
    """Removes the contents at the path, if it exists"""
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            os.remove(path)


def get_path_size_bytes(path: Path) -> int:
    size_bytes = 0
    file_paths = deque(find_all_paths(path, include_dirs=False, include_files=True))
    while file_paths:
        file_path = file_paths.popleft()
        path = Path(file_path)
        try:
            size_bytes += path.stat().st_size
        except FileNotFoundError as e:
            logger.warning(f"File at {path} does not exist anymore. Reason: {e}")
            continue
        except OSError as ose:
            if ose.errno == errno.ESTALE:
                logger.warning(f"{ose} raised for {file_path}.")
                if path.exists():
                    logger.warning(f"Adding {path} to end of list to check later.")
                    file_paths.append(file_path)
            else:
                logger.error(f"Unexpected error raised for {path}. Reason: {ose}")
                raise ose
    return size_bytes


def get_path_hash(
    path: Union[Path, str],
    includes: Optional[Sequence[Union[Pattern, str]]] = None,
    excludes: Optional[Sequence[Union[Pattern, str]]] = None,
) -> str:
    """Generate the hash based on files found under a given path.

    Args:
        path (str): path to compute a hash
        includes (Sequence[str], optional): list of regex patterns to include. Defaults to all.
        excludes (Sequence[str], optional): list of regex patterns to exclude. Defaults to None.

    Returns:
        str: hash value
    """
    paths_to_hash = find_paths(root=path, include_dirs=False, includes=includes, excludes=excludes)

    path_hash = hashlib.sha256()
    for path in paths_to_hash:
        path_hash.update(sha256sum(path).encode("utf-8"))

    return path_hash.hexdigest()


def find_paths(
    root: Union[str, Path],
    include_dirs: bool = True,
    include_files: bool = True,
    includes: Optional[Sequence[Union[Pattern, str]]] = None,
    excludes: Optional[Sequence[Union[Pattern, str]]] = None,
) -> List[str]:
    """Find paths that match criteria

    Args:
        root (Union[str, Path]): root path
        include_dirs (bool, optional): whether to include directories. Defaults to True.
        include_files (bool, optional): whether to include files. Defaults to True.

        includes (Sequence[str], optional): list of regex patterns to include. Defaults to all.
        excludes (Sequence[str], optional): list of regex patterns to exclude. Defaults to None.

    Returns:
        List[str]: list of paths matching criteria
    """

    paths_to_return = []
    paths = find_all_paths(root, include_dirs=include_dirs, include_files=include_files)

    if not includes and not excludes:
        return paths

    include_patterns = [re.compile(include) for include in includes or [r".*"]]
    exclude_patterns = [re.compile(exclude) for exclude in excludes or []]

    for path in paths:
        target_path = path  # if check_absolute_path else strip_path_root(root=root, path=path)
        # First check exclude patterns
        for exclude_pattern in exclude_patterns:
            if exclude_pattern.fullmatch(target_path):
                break
        else:
            # Now check include patterns
            for include_pattern in include_patterns:
                if include_pattern.fullmatch(target_path):
                    paths_to_return.append(path)
                    break
    return paths_to_return


def get_path_with_root(path: Union[str, Path], root: Union[str, Path]) -> str:
    orig_path, orig_root = path, root
    root = Path(root)
    path = Path(path)
    if path.is_relative_to(root):
        return str(orig_path)
    rel_path = path.relative_to("/") if path.is_absolute() else path
    path_with_root = os.path.normpath(root / rel_path)
    return path_with_root


def strip_path_root(path: Union[str, Path], root: Optional[Union[str, Path]] = None) -> str:
    """Strip the root from the path if path is absolute

    Args:
        path (Union[str, Path]): path to strip root from
        root (Optional[Union[str, Path]], optional): optionally specify root.
            If no root specified, uses "/".

    Returns:
        str: a relative path
    """
    root = Path(root) if root is not None else Path("/")
    path = Path(path)
    rel_path = path.relative_to(root) if path.is_absolute() else path
    return os.path.normpath(rel_path)


class CannotAcquirePathLockError(Exception):
    pass


@dataclass
class PathLock:
    """
    A context manager for acquiring and releasing locks on a file or directory path.

    If lock_root is provided, a lock file will be created in that directory with the name of the hash of the path.
    If lock_root is not provided, a lock file with the same name as the path and a .lock extension will be created.

    Providing an explicit lock root is useful if you dont want processes to read the lock file
    from the same directory as the file being locked.

    Attributes:
        path (Union[str, Path]): The path to the file.
        lock_root (Optional[Union[str, Path]]): The root directory for lock files. If provided, a
            lock file will be created in this directory with the name of the hash of the path.
            Otherwise, a lock file with the same name as the path and a .lock extension
            will be created. Defaults to None.
    """

    path: Union[str, Path]
    lock_root: Optional[Union[str, Path]] = None
    raise_if_locked: bool = False

    def __post_init__(self):
        # If lock root is provided, then create a lock file in that directory
        # with the name of the hash of the path. Otherwise, create a lock file
        # with the same name as the path with a .lock extension.
        if self.lock_root:
            lock_file_name = f"{hashlib.sha256(str(self.path).encode()).hexdigest()}.lock"
            self._lock_path = Path(self.lock_root) / lock_file_name
        else:
            self._lock_path = Path(f"{self.path}.lock")
        self._lock_file = None
        logger.info(f"Created {self} with {self._lock_path} lock file")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exec_type, exec_val, exec_tb):
        self.release()

    def acquire(self):
        logger.info(f"Acquiring lock...")
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
            self._lock_file = open(self._lock_path, "w")
            op = fcntl.LOCK_EX
            if self.raise_if_locked:
                op |= fcntl.LOCK_NB
            fcntl.flock(self._lock_file, op)
            self._lock_file.write(f"{datetime.now().timestamp()}")
            logger.info(f"Lock acquired!")
        except Exception as e:
            msg = f"Could not acquire lock! Reason: {e}"
            logger.error(msg)
            raise CannotAcquirePathLockError(msg) from e

    def release(self):
        logger.info(f"Releasing lock...")

        if self._lock_file and not self._lock_file.closed:
            try:
                fcntl.flock(self._lock_file, fcntl.LOCK_UN)
                self._lock_file.close()
            except Exception as e:
                logger.warning(f"Lock file doesn't exist. Skipping fcntl.flock and close: {e}")
        else:
            logger.warning("Strange! lock file already closed. not calling fcntl.flock")
        logger.info("Removing lock file")
        remove_path(self._lock_path)

        logger.info("Lock released!")


# ---------------
# Helpers


def sha256sum(filename: str, bufsize: int = 128 * 1024) -> str:
    """

    https://stackoverflow.com/a/70215084/4544508

    Args:
        filename (str): file to hash
        bufsize (int, optional): buffer size. Defaults to 128*1024.

    Returns:
        str: hash value of file
    """
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
