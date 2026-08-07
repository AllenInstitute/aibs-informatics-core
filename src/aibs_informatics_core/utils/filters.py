"""Shared include/exclude path filtering.

This module defines the single filtering contract used across data sync
(local, S3, and EFS listings). Historically each call site rolled its own
variation -- some matched against the relative path, some against the full
absolute path, some used :meth:`re.Pattern.match` and some
:meth:`re.Pattern.fullmatch`. That meant a pattern such as ``sample/.*``
filtered under S3 and silently did nothing under a local root.

The contract implemented here is:

- Patterns are **regular expressions** (not glob patterns).
- A pattern is matched with :meth:`re.Pattern.fullmatch`, so it must describe
  the *entire* path, not a fragment of it. Use ``.*`` explicitly to match a
  fragment (e.g. ``.*\\.bam``).
- Paths are matched **relative to a supplied root**, so patterns are portable
  across the absolute location the data happens to live at.
- **Exclude wins over include**: a path matching any exclude pattern is dropped
  regardless of the include patterns.
- An absent or empty ``include`` includes everything.
"""

__all__ = [
    "compile_patterns",
    "get_relative_path",
    "path_matches_filters",
    "filter_paths",
]

import re
from collections.abc import Iterable, Sequence
from os.path import basename
from pathlib import Path
from re import Pattern

Patterns = str | Pattern | Sequence[str | Pattern] | None


def compile_patterns(patterns: Patterns) -> list[Pattern] | None:
    """Normalize pattern input into a list of compiled regex patterns.

    Accepts a single pattern or a sequence of patterns, either as strings or
    as already-compiled :class:`re.Pattern` objects.

    Args:
        patterns: Pattern(s) to compile. May be ``None`` or empty.

    Returns:
        A list of compiled patterns, or ``None`` if no patterns were given.
    """
    if not patterns:
        return None
    if isinstance(patterns, (str, Pattern)):
        patterns = [patterns]
    return [p if isinstance(p, Pattern) else re.compile(p) for p in patterns]


def get_relative_path(path: str | Path, root: str | Path | None = None) -> str:
    """Get the path relative to the filter root, as a string.

    This is intentionally string prefix based rather than :mod:`pathlib` based
    so that it works unchanged for URI style paths (e.g. ``s3://bucket/key``),
    which :class:`pathlib.Path` would mangle by collapsing ``//``.

    Args:
        path: The path to relativize.
        root: The root to relativize against. If ``None``, ``path`` is returned
            unchanged (i.e. it is assumed to already be relative).

    Returns:
        The path relative to ``root``. If ``path`` *is* ``root`` -- which
        happens when the sync source is a single file or object -- the base
        name is returned, so that patterns still have something to match. If
        ``path`` does not live under ``root`` at all, it is returned unchanged.
    """
    str_path = str(path)
    if root is None:
        return str_path

    str_root = str(root).rstrip("/")
    if not str_root:
        return str_path.lstrip("/")
    if str_path == str_root:
        return basename(str_path)
    prefix = f"{str_root}/"
    if str_path.startswith(prefix):
        return str_path[len(prefix) :]
    return str_path


def path_matches_filters(
    path: str | Path,
    root: str | Path | None = None,
    include: Patterns = None,
    exclude: Patterns = None,
) -> bool:
    """Check whether a path passes the include/exclude filters.

    See the module docstring for the full contract. In short: patterns are
    regexes matched with ``fullmatch`` against ``path`` relative to ``root``,
    exclude wins over include, and an empty include includes everything.

    Args:
        path: The path to test.
        root: Root that ``path`` is matched relative to. If ``None``, ``path``
            is matched as given.
        include: Pattern(s) a path must match to be kept. Defaults to all.
        exclude: Pattern(s) that drop a path. Takes precedence over ``include``.

    Returns:
        True if the path should be kept.
    """
    include_patterns = compile_patterns(include)
    exclude_patterns = compile_patterns(exclude)
    if include_patterns is None and exclude_patterns is None:
        return True
    return _matches(
        get_relative_path(path, root),
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )


def filter_paths(
    paths: Iterable[str | Path],
    root: str | Path | None = None,
    include: Patterns = None,
    exclude: Patterns = None,
) -> list[str]:
    """Filter an iterable of paths with the include/exclude filters.

    Equivalent to calling :func:`path_matches_filters` for each path, but the
    patterns are only compiled once.

    Args:
        paths: The paths to filter.
        root: Root that each path is matched relative to. If ``None``, paths
            are matched as given.
        include: Pattern(s) a path must match to be kept. Defaults to all.
        exclude: Pattern(s) that drop a path. Takes precedence over ``include``.

    Returns:
        The paths that passed the filters, as strings, in their original order.
    """
    include_patterns = compile_patterns(include)
    exclude_patterns = compile_patterns(exclude)
    if include_patterns is None and exclude_patterns is None:
        return [str(path) for path in paths]
    return [
        str(path)
        for path in paths
        if _matches(
            get_relative_path(path, root),
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
    ]


def _matches(
    relative_path: str,
    include_patterns: list[Pattern] | None,
    exclude_patterns: list[Pattern] | None,
) -> bool:
    """Apply compiled patterns to an already relativized path."""
    if exclude_patterns and any(p.fullmatch(relative_path) for p in exclude_patterns):
        return False
    if not include_patterns:
        return True
    return any(p.fullmatch(relative_path) for p in include_patterns)
