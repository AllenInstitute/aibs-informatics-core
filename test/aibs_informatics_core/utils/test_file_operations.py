import errno
import os
import tarfile
import zipfile
from pathlib import Path
from typing import List, Literal, Sequence, Tuple, Union
from unittest.mock import MagicMock, patch

from aibs_informatics_test_resources import BaseTest, does_not_raise
from pytest import mark, param, raises

from aibs_informatics_core.utils.file_operations import (
    ArchiveType,
    PathLock,
    copy_path,
    extract_archive,
    get_path_hash,
    get_path_size_bytes,
    get_path_with_root,
    make_archive,
    move_path,
    remove_path,
    strip_path_root,
)


class FileOperationsBaseTest(BaseTest):
    def assertDirectoryContents(self, root_path: Path, expected_file_paths: List[str]):
        relative_extracted_paths = [
            str(_) for _ in self.os_walk(root_path, include_dirs=False, include_root=False)
        ]
        self.assertListEqual(relative_extracted_paths, sorted(expected_file_paths))

    def create_tar_archive(
        self,
        root_path: Path,
        relative_paths: List[str] = [],
        compression: Literal["", "gz"] = "gz",
    ) -> Path:
        self.create_dir(root_path, relative_paths)

        tar_name = self.tmp_path() / "archive"
        with tarfile.open(tar_name, f"w:{compression}") as tar_handle:
            for relative_root, dirs, files in os.walk(root_path):
                rel_root_path = Path(relative_root)
                for file in files:
                    arcname = (rel_root_path / file).relative_to(root_path)
                    tar_handle.add(os.path.join(relative_root, file), arcname=arcname)
        return tar_name

    def create_zip_archive(self, root_path: Path, relative_paths: List[str] = []) -> Path:
        self.create_dir(root_path, relative_paths)

        zip_name = self.tmp_path() / "archive"
        with zipfile.ZipFile(zip_name, "w") as zipf:
            for relative_root, dirs, files in os.walk(root_path):
                rel_root_path = Path(relative_root)
                for file in files:
                    arcname = (rel_root_path / file).relative_to(root_path)
                    zipf.write(os.path.join(relative_root, file), arcname=arcname)
        return zip_name

    def create_dir(self, root_path: Path, relative_paths: Sequence[Union[str, Tuple[str, str]]]):
        for relative_path in relative_paths:
            relative_path, content = (
                relative_path
                if isinstance(relative_path, tuple)
                else (relative_path, relative_path)
            )
            path = root_path / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def os_walk(
        self,
        root_path: Path,
        include_dirs: bool = True,
        include_files: bool = True,
        include_root: bool = True,
    ) -> List[Path]:
        paths = []
        for relative_root, dirs, files in os.walk(root_path):
            rel_root_path = Path(relative_root)
            if include_dirs:
                paths.extend([rel_root_path / d for d in dirs])

            if include_files:
                paths.extend([rel_root_path / f for f in files])
        if not include_root:
            paths = [_.relative_to(root_path) for _ in paths]
        return sorted(paths)


class ArchiveTests(FileOperationsBaseTest):
    def test__is_archive__works(self):
        path = self.create_tar_archive(self.tmp_path(), ["a.txt", "b.txt"])
        self.assertTrue(ArchiveType.is_archive(path))

        # Invalid cases: non-existent path, non-archive path
        path = self.tmp_file()
        self.assertFalse(ArchiveType.is_archive(path))

        path.touch()
        self.assertFalse(ArchiveType.is_archive(path))

    def test__is_archive_type__works(self):
        path = self.create_tar_archive(self.tmp_path(), ["a.txt", "b.txt"])
        self.assertTrue(ArchiveType.TAR_GZ.is_archive_type(path))
        path = self.tmp_file()
        self.assertFalse(ArchiveType.TAR_GZ.is_archive_type(path))

    def test__extract_archive__extracts_tar_gz__no_dest_provided(self):
        paths = ["a.txt", "b.txt"]
        archive_path = self.create_tar_archive(self.tmp_path(), paths)
        extracted_path = extract_archive(archive_path)

        self.assertDirectoryContents(extracted_path, paths)

    def test__extract_archive__extracts_tar__no_dest_provided(self):
        paths = ["a.txt", "b.txt"]
        archive_path = self.create_tar_archive(self.tmp_path(), paths, compression="")
        extracted_path = extract_archive(archive_path)

        self.assertDirectoryContents(extracted_path, paths)

    def test__extract_archive__extracts_zip__no_dest_provided(self):
        paths = ["a.txt", "b.txt"]
        archive_path = self.create_zip_archive(self.tmp_path(), paths)
        extracted_path = extract_archive(archive_path)

        self.assertDirectoryContents(extracted_path, paths)

    def test__extract_archive__extracts_tar_gz__to_dest_path(self):
        paths = ["a.txt", "b.txt", "c/c.txt"]

        archive_path = self.create_tar_archive(self.tmp_path(), paths)
        intended_extracted_path = self.tmp_path()
        extracted_path = extract_archive(archive_path, intended_extracted_path)
        self.assertEqual(intended_extracted_path, extracted_path)

        self.assertDirectoryContents(extracted_path, paths)

    def test__make_archive__makes_tar_gz_in_tmp_file_as_default(self):
        dir_path = self.tmp_path()
        paths = ["a.txt", "b.txt", "c/c.txt"]
        self.create_dir(dir_path, paths)
        dest_path = make_archive(dir_path)
        self.assertEqual(ArchiveType.TAR_GZ, ArchiveType.from_path(dest_path))

    def test__make_archive__makes_tar_gz_and_moves_to_specified_path_when_specified(self):
        dir_path = self.tmp_path()
        archive_path = self.tmp_path() / "some_path"
        paths = ["a.txt", "b.txt", "c/c.txt"]
        self.create_dir(dir_path, paths)
        dest_path = make_archive(dir_path, destination_path=archive_path)
        self.assertEqual(f"{archive_path}", f"{dest_path}")

    def test__make_archive__makes_tar_gz_at_directly_path_when_suffixed_correctly(self):
        dir_path = self.tmp_path()
        archive_path = self.tmp_path() / "some_path.tar.gz"
        paths = ["a.txt", "b.txt", "c/c.txt"]
        self.create_dir(dir_path, paths)
        dest_path = make_archive(dir_path, destination_path=archive_path)
        self.assertEqual(f"{archive_path}", f"{dest_path}")

    def test__make_archive__makes_archive_in_specified_format(self):
        dir_path = self.tmp_path()
        paths = ["a.txt", "b.txt", "c/c.txt"]
        self.create_dir(dir_path, paths)
        options = ["bztar", "tar", "gztar", "xztar", "zip", ArchiveType.ZIP]
        for fmt in options:
            dest_path = make_archive(dir_path, archive_type=fmt)
            self.assertEqual(ArchiveType(fmt), ArchiveType.from_path(dest_path))

    def test__make_archive__extract_archive__works_as_intended(self):
        dir_path = self.tmp_path()
        new_dir_path = self.tmp_path()
        paths = ["a.txt", "b.txt", "c/c.txt"]
        self.create_dir(dir_path, paths)
        archive_path = make_archive(dir_path)
        actual_dir_path = extract_archive(archive_path, destination_path=new_dir_path)
        self.assertDirectoryContents(new_dir_path, paths)

    def test__make_archive__fails_for_bad_path(self):
        with self.assertRaises(ValueError):
            make_archive(self.tmp_path() / "non-existent-path")


class FileOperationsTests(FileOperationsBaseTest):
    def setUp(self) -> None:
        super().setUp()

    def get_path_to_hash(self) -> Path:
        asset_path = self.tmp_path()
        (asset_path / "a.py").write_text('a = "hello"')
        (asset_path / "b.py").write_text('b = "bye"')
        (asset_path / "x.txt").write_text("I'm a simple txt file")
        (asset_path / "dir1").mkdir(exist_ok=True)
        (asset_path / "dir1" / "__init__.py").touch()
        (asset_path / "dir1" / "a.py").write_text('a = "hello"')
        (asset_path / "dir1" / "b.py").write_text('b = "bye"')
        (asset_path / "dir1" / "c.py").write_text('c = ""')
        return asset_path

    def test__get_path_hash__changes_when_file_added_and_no_filters_applied(self):
        asset_path = self.get_path_to_hash()
        original_hash = get_path_hash(str(asset_path))
        (asset_path / "c.py").write_text("c = 'hallo'")
        new_hash = get_path_hash(str(asset_path))
        assert original_hash != new_hash

    def test__get_path_hash__does_not_change_when_file_added_but_excluded(self):
        excludes = [r".*\.txt"]
        asset_path = self.get_path_to_hash()
        original_hash = get_path_hash(str(asset_path), excludes=excludes)
        (asset_path / "dir1" / "c.txt").write_text("c = 'hallo'")
        new_hash = get_path_hash(str(asset_path), excludes=excludes)
        assert original_hash == new_hash

    def test__get_path_hash__does_not_change_when_file_added_but_not_included(
        self,
    ):
        includes = [r".*\.txt"]
        asset_path = self.get_path_to_hash()
        original_hash = get_path_hash(str(asset_path), includes=includes)
        (asset_path / "c.py").write_text("c = 'hallo'")
        new_hash = get_path_hash(str(asset_path), includes=includes)
        assert original_hash == new_hash

    def test__get_path_hash__does_not_change_because_excludes_supersedes_includes(
        self,
    ):
        excludes = [r".*\.txt"]
        asset_path = self.get_path_to_hash()
        original_hash = get_path_hash(str(asset_path), includes=excludes, excludes=excludes)
        (asset_path / "dir1" / "c.txt").write_text("c = 'hallo'")
        new_hash = get_path_hash(str(asset_path), includes=excludes, excludes=excludes)
        assert original_hash == new_hash

    def test__get_path_size_bytes__handles_dir(self):
        path = self.tmp_path()
        self.create_dir(path, [("a", "_" * 1), ("b", "_" * 1), ("dir/a", "_" * 1)])
        self.assertEqual(get_path_size_bytes(path), 3)

    def test__get_path_size_bytes__handles_empty_dir(self):
        path = self.tmp_path()
        self.assertEqual(get_path_size_bytes(path), 0)

    def test__get_path_size_bytes__handles_file(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        self.assertEqual(get_path_size_bytes(path), 5)

    @patch("aibs_informatics_core.utils.file_operations.find_all_paths")
    @patch("aibs_informatics_core.utils.file_operations.Path")
    def test__get_path_size_bytes__handles_errors(self, mock_Path, mock_find_all_paths):
        mock_find_all_paths.return_value = ["a", "b"]
        path = self.tmp_path()
        e1 = MagicMock()
        e1.stat.side_effect = FileNotFoundError()
        e2 = MagicMock()
        ose = OSError()
        ose.errno = errno.ESTALE
        e2.stat.side_effect = ose

        e2.exists.side_effect = [True, False]
        mock_Path.side_effect = [e1, e2, e2]
        self.assertEqual(get_path_size_bytes(path), 0)

        with self.assertRaises(OSError):
            ose.errno = errno.ETIME
            e1.stat.side_effect = ose
            mock_find_all_paths.return_value = ["a"]
            mock_Path.side_effect = [e1]
            get_path_size_bytes(path)

    def test__move_path__handles_file(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        path_content = path.read_text()
        new_path = self.tmp_file()
        self.assertFalse(new_path.exists())
        move_path(path, new_path)
        self.assertFalse(path.exists())
        self.assertTrue(new_path.exists())
        self.assertEqual(new_path.read_text(), path_content)

    def test__move_path__handles_file__destination_exists(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        path_content = path.read_text()
        new_path = self.tmp_file()
        new_path.touch()
        self.assertTrue(new_path.exists())
        self.assertNotEqual(new_path.read_text(), path_content)
        with self.assertRaises(ValueError):
            move_path(path, new_path)
        move_path(path, new_path, exists_ok=True)
        self.assertEqual(new_path.read_text(), path_content)

    def test__move_path__handles_dir(self):
        root = self.tmp_path()
        (path := root / "old").mkdir()
        (path / "a").write_text("a" * 5)
        (path / "b").write_text("b" * 5)
        new_path = self.tmp_path() / "new"
        self.assertFalse(new_path.exists())
        move_path(path, new_path)
        self.assertFalse(path.exists())
        self.assertTrue(new_path.exists())
        self.assertDirectoryContents(new_path, ["a", "b"])

    def test__copy_path__handles_file(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        new_path = self.tmp_file()
        self.assertFalse(new_path.exists())
        copy_path(path, new_path)
        self.assertTrue(new_path.exists())
        self.assertEqual(new_path.read_text(), path.read_text())

    def test__copy_path__handles_file__destination_exists(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        new_path = self.tmp_file()
        new_path.touch()
        self.assertTrue(new_path.exists())
        self.assertNotEqual(new_path.read_text(), path.read_text())
        with self.assertRaises(ValueError):
            copy_path(path, new_path)
        copy_path(path, new_path, exists_ok=True)
        self.assertEqual(new_path.read_text(), path.read_text())

    def test__copy_path__handles_dir(self):
        root = self.tmp_path()
        (path := root / "old").mkdir()
        (path / "a").write_text("a" * 5)
        (path / "b").write_text("b" * 5)
        new_path = self.tmp_path() / "new"
        self.assertFalse(new_path.exists())
        copy_path(path, new_path)
        self.assertTrue(new_path.exists())
        self.assertDirectoryContents(new_path, ["a", "b"])

    def test__remove_path__handles_file(self):
        path = self.tmp_file()
        path.write_text("_" * 5)
        self.assertTrue(path.exists())
        remove_path(path)
        self.assertFalse(path.exists())

    def test__remove_path__handles_dir(self):
        path = self.tmp_path()
        (path / "a").write_text("_" * 5)
        self.assertTrue(path.exists())
        remove_path(path)
        self.assertFalse(path.exists())

    def test__remove_path__handles_empty(self):
        path = self.tmp_file()
        self.assertFalse(path.exists())
        remove_path(path)
        self.assertFalse(path.exists())

    def test__PathLock__locks_folder(self):
        path = self.tmp_path()
        with PathLock(path) as lock:
            lock_path = lock._lock_path
            self.assertTrue(lock_path.exists())
        self.assertFalse(lock_path.exists())

    def test__PathLock__handles_stale_lock_file(self):
        path = self.tmp_path()
        with PathLock(path) as lock:
            lock_path = lock._lock_path
            self.assertTrue(lock_path.exists())
            if lock._lock_file:
                lock._lock_file.close()
        lock.release()
        self.assertFalse(lock_path.exists())

    def test__PathLock__fails_if_lock_aquired(self):
        path = self.tmp_path()
        with PathLock(path) as lock:
            with self.assertRaises(Exception):
                with PathLock(path) as lock2:
                    pass


@mark.parametrize(
    "path, root, expected",
    [
        param(Path("file"), Path("/path/to/"), "/path/to/file", id="simple file [P/P]"),
        param(
            Path("/path/to/file"),
            Path("/path/to/"),
            "/path/to/file",
            id="file path already has correct prefix (Path, Path)",
        ),
    ],
)
def test__get_path_with_root(path: Union[Path, str], root: Union[Path, str], expected: str):
    actual = get_path_with_root(path=path, root=root)
    assert actual == expected


@mark.parametrize(
    "path, root, expected, expectation",
    [
        param("/A/a", None, "A/a", does_not_raise(), id="strips path using default root"),
        param(Path("a"), Path("/A/a"), "a", does_not_raise(), id="no-op for relative path"),
        param("a", Path("/A/a"), "a", does_not_raise(), id="no-op for relative str path"),
        param("/A/a", Path("/A"), "a", does_not_raise(), id="strips path"),
        param("/A/a", Path("/B"), None, raises(ValueError), id="raises error for invalid root"),
    ],
)
def test__strip_path_root__works(path, root, expected, expectation):
    with expectation:
        actual = strip_path_root(path, root)
    if expected is not None:
        assert actual == expected
