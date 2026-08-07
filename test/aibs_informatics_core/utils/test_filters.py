import re
from pathlib import Path

import pytest

from aibs_informatics_core.utils.filters import (
    compile_patterns,
    filter_paths,
    get_relative_path,
    path_matches_filters,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param(None, None, id="none"),
        pytest.param("", None, id="empty string"),
        pytest.param([], None, id="empty list"),
        pytest.param(r".*\.txt", [r".*\.txt"], id="single string"),
        pytest.param([r"a.*", r"b.*"], [r"a.*", r"b.*"], id="list of strings"),
    ],
)
def test__compile_patterns__normalizes_input(value, expected):
    actual = compile_patterns(value)
    if expected is None:
        assert actual is None
    else:
        assert [p.pattern for p in actual] == expected


def test__compile_patterns__passes_through_compiled_patterns():
    pattern = re.compile(r".*\.txt")
    assert compile_patterns(pattern) == [pattern]
    assert compile_patterns([pattern, r"b.*"]) == [pattern, re.compile(r"b.*")]


@pytest.mark.parametrize(
    "path, root, expected",
    [
        pytest.param("/a/b/c.txt", None, "/a/b/c.txt", id="no root returns path as is"),
        pytest.param("/a/b/c.txt", "/a", "b/c.txt", id="strips root"),
        pytest.param("/a/b/c.txt", "/a/", "b/c.txt", id="strips root with trailing slash"),
        pytest.param(Path("/a/b/c.txt"), Path("/a"), "b/c.txt", id="accepts path objects"),
        pytest.param(
            "s3://bucket/run1/s1/c.bam",
            "s3://bucket/run1",
            "s1/c.bam",
            id="handles s3 uris without mangling scheme",
        ),
        pytest.param(
            "s3://bucket/run1/s1/c.bam",
            "s3://bucket/run1/",
            "s1/c.bam",
            id="handles s3 uris with trailing slash",
        ),
        pytest.param("/a/b/c.txt", "/a/b/c.txt", "c.txt", id="path is root uses base name"),
        pytest.param("/a/b/c.txt", "/x", "/a/b/c.txt", id="path not under root is unchanged"),
    ],
)
def test__get_relative_path(path, root, expected):
    assert get_relative_path(path, root) == expected


def test__path_matches_filters__anchors_patterns_relative_to_root():
    # The pattern describes the path relative to the root, not its absolute location.
    assert path_matches_filters("/data/run1/s1/a.bam", root="/data/run1", include=r"s1/.*")
    assert not path_matches_filters("/data/run1/s2/a.bam", root="/data/run1", include=r"s1/.*")
    # Without relative anchoring the same pattern would need the absolute prefix, which it
    # no longer matches.
    assert not path_matches_filters(
        "/data/run1/s1/a.bam", root="/data/run1", include=r"/data/run1/s1/.*"
    )


def test__path_matches_filters__uses_fullmatch_not_search():
    assert path_matches_filters("a.txt", include=r".*\.txt")
    # A fragment does not match -- the pattern must describe the entire path.
    assert not path_matches_filters("a.txt", include=r"\.txt")
    assert not path_matches_filters("sub/a.txt", include=r"a\.txt")


def test__path_matches_filters__exclude_beats_include():
    assert not path_matches_filters("a.txt", include=r".*\.txt", exclude=r"a\.txt")
    assert path_matches_filters("b.txt", include=r".*\.txt", exclude=r"a\.txt")


@pytest.mark.parametrize("include", [None, "", []], ids=["none", "empty string", "empty list"])
def test__path_matches_filters__empty_include_includes_everything(include):
    assert path_matches_filters("anything/at/all.bam", include=include)
    # ... but an exclude still applies.
    assert not path_matches_filters("anything/at/all.bam", include=include, exclude=r".*\.bam")


def test__path_matches_filters__no_filters_matches_everything():
    assert path_matches_filters("/a/b/c.txt")
    assert path_matches_filters("/a/b/c.txt", root="/x")


def test__path_matches_filters__multiple_patterns_are_ored():
    assert path_matches_filters("a.txt", include=[r".*\.txt", r".*\.csv"])
    assert path_matches_filters("a.csv", include=[r".*\.txt", r".*\.csv"])
    assert not path_matches_filters("a.log", include=[r".*\.txt", r".*\.csv"])
    assert not path_matches_filters("a.log", exclude=[r".*\.log", r".*\.tmp"])


def test__filter_paths__filters_relative_to_root():
    paths = [
        "/data/run1/s1/a.bam",
        "/data/run1/s1/a.bai",
        "/data/run1/s2/b.bam",
    ]
    actual = filter_paths(paths, root="/data/run1", include=r"s1/.*")
    assert actual == ["/data/run1/s1/a.bam", "/data/run1/s1/a.bai"]


def test__filter_paths__exclude_beats_include_and_preserves_order():
    paths = ["/r/c.txt", "/r/a.txt", "/r/b.txt", "/r/d.log"]
    actual = filter_paths(paths, root="/r", include=r".*\.txt", exclude=r"b\.txt")
    assert actual == ["/r/c.txt", "/r/a.txt"]


def test__filter_paths__no_filters_returns_all_paths_as_strings():
    paths = [Path("/r/a.txt"), "/r/b.txt"]
    assert filter_paths(paths) == ["/r/a.txt", "/r/b.txt"]


def test__filter_paths__empty_include_includes_everything():
    paths = ["/r/a.txt", "/r/b.log"]
    assert filter_paths(paths, root="/r", include=[]) == paths
    assert filter_paths(paths, root="/r", include=[], exclude=r".*\.log") == ["/r/a.txt"]
