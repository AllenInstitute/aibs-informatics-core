#!/usr/bin/env bash
#
# Best-effort backfill of versioned documentation for tags that were released
# before mike-based doc versioning was introduced.
#
# For each tag, the docs are built in a throwaway git worktree checked out at
# that tag and deployed to the docs branch under its X.Y version. Nothing is
# pushed unless --push is passed, so you can review the result locally first:
#
#     scripts/backfill-docs-versions.sh
#     make docs-serve-versions
#     scripts/backfill-docs-versions.sh --push
#
# With no TAGs, every v* tag is considered, keeping only the highest patch of
# each X.Y -- docs are versioned per minor release, matching release.yml. The
# `latest` and `dev` aliases are never touched; they belong to the release and
# main-branch workflows.
#
# Old tags are expected to fail: they may predate mkdocs.yml, the `docs`
# dependency group, or uv itself. Failures are reported and skipped, never
# fatal.
#
# Versions that already exist on the docs branch are left alone -- they are
# managed by CI -- unless --force is passed.
#
# Usage: scripts/backfill-docs-versions.sh [--push] [--force] [TAG ...]

set -euo pipefail

DOCS_BRANCH="${DOCS_BRANCH:-gh-pages}"
DOCS_REMOTE="${DOCS_REMOTE:-origin}"
PUSH=false
FORCE=false

while [ $# -gt 0 ]; do
	case "$1" in
	--push)
		PUSH=true
		shift
		;;
	--force)
		FORCE=true
		shift
		;;
	-h | --help)
		sed -n '2,27p' "$0"
		exit 0
		;;
	-*)
		echo "unknown option: $1" >&2
		exit 2
		;;
	*) break ;;
	esac
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/backfill-docs.XXXXXX")"
TAG_FILE="$WORK_DIR/tags"
RESULT_FILE="$WORK_DIR/results"
: >"$RESULT_FILE"

cleanup() {
	# Drop the directories first, then let git discard their registrations.
	# Matching them by path is unreliable (on macOS mktemp hands back /var/...
	# while git records the resolved /private/var/...).
	rm -rf "$WORK_DIR"
	git worktree prune >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [ $# -gt 0 ]; then
	printf '%s\n' "$@" >"$TAG_FILE"
else
	# Highest patch release of each X.Y, oldest minor first.
	git tag --list 'v*' |
		sort -V |
		awk -F. '{ key = $1 "." $2
		           if (!(key in latest)) { order[++n] = key }
		           latest[key] = $0 }
		         END { for (i = 1; i <= n; i++) print latest[order[i]] }' >"$TAG_FILE"
fi

if [ ! -s "$TAG_FILE" ]; then
	echo "No v* tags found." >&2
	exit 1
fi

# True when the docs branch already carries an entry for this version.
already_deployed() {
	git show "$DOCS_BRANCH:versions.json" 2>/dev/null |
		python3 -c 'import json, sys
try:
    versions = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
sys.exit(0 if sys.argv[1] in {v.get("version") for v in versions} else 1)' "$1"
}

# mike compares against the remote before committing, so make sure we have it.
git fetch "$DOCS_REMOTE" "$DOCS_BRANCH" 2>/dev/null ||
	echo "note: no $DOCS_REMOTE/$DOCS_BRANCH yet; it will be created"

while IFS= read -r tag; do
	[ -n "$tag" ] || continue
	version="$(printf '%s' "$tag" | sed -E 's/^v//; s/^([0-9]+\.[0-9]+).*/\1/')"
	echo
	echo "=== $tag -> version $version"

	worktree="$WORK_DIR/wt-$version"
	rm -rf "$worktree"
	if ! git worktree add --detach --quiet "$worktree" "$tag"; then
		printf '%-12s SKIPPED  cannot check out tag\n' "$tag" >>"$RESULT_FILE"
		continue
	fi

	if [ ! -f "$worktree/mkdocs.yml" ]; then
		printf '%-12s SKIPPED  no mkdocs.yml at this tag\n' "$tag" >>"$RESULT_FILE"
		continue
	fi

	# Never overwrite a version CI already published (and never leave the alias
	# copy it points at stale) unless explicitly asked to.
	if [ "$FORCE" != true ] && already_deployed "$version"; then
		printf '%-12s SKIPPED  %s already on %s (use --force)\n' "$tag" "$version" "$DOCS_BRANCH" >>"$RESULT_FILE"
		continue
	fi

	push_flag=""
	[ "$PUSH" = true ] && push_flag="--push"

	# The tag's own pyproject.toml predates mike, so bring it along with --with.
	if (cd "$worktree" && uv run --with mike --group docs \
		mike deploy \
		--branch "$DOCS_BRANCH" --remote "$DOCS_REMOTE" \
		--alias-type=copy --title "$version" \
		${push_flag} "$version"); then
		printf '%-12s OK       deployed as %s\n' "$tag" "$version" >>"$RESULT_FILE"
	else
		printf '%-12s FAILED   docs build or deploy failed (see output above)\n' "$tag" >>"$RESULT_FILE"
	fi
done <"$TAG_FILE"

echo
echo "=== Summary"
cat "$RESULT_FILE"
echo
if [ "$PUSH" = true ]; then
	echo "Pushed to $DOCS_REMOTE/$DOCS_BRANCH."
else
	echo "Nothing pushed. Review with 'make docs-serve-versions', then re-run with --push."
fi
