# Developer Guide

This guide provides information for developers who want to contribute to the AIBS Informatics Core library.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Make (optional, but recommended)

### Clone the Repository

```bash
git clone https://github.com/AllenInstitute/aibs-informatics-core.git
cd aibs-informatics-core
```

### Install Dependencies

Using make:

```bash
make install
```

Using uv directly:

```bash
uv sync --group dev
```

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test coverage-server

# Run specific test file
pytest test/aibs_informatics_core/test_collections.py
```

## Code Quality

### Linting

```bash
# Run ruff linter
make lint

# Auto-fix linting issues
make format
```

### Type Checking

```bash
# Run mypy type checker
make lint-mypy
```

## Building Documentation

```bash
# Serve documentation locally
make docs-serve

# Build documentation
make docs-build
```

### Versioned documentation

The published site keeps one entry per minor release alongside a `dev` build, using [mike](https://github.com/jimporter/mike). The version selector in the site header switches between them.

| URL | Contents |
| --- | --- |
| `/` | Redirect to `latest/` |
| `latest/` | The newest release (an alias for the highest `X.Y`) |
| `X.Y/` | Built from that minor version's most recent release tag |
| `dev/` | Built from the tip of `main` |

Publishing is automatic:

- Pushes to `main` redeploy `dev` (`.github/workflows/publish_docs.yml`).
- A release redeploys its `X.Y` version and moves the `latest` alias (the `publish-docs` job in `.github/workflows/release.yml`). It builds from the release tag, so published docs match the released code. Patch releases refresh their minor version rather than adding an entry.

To preview or publish by hand:

```bash
# Serve every published version, with the version selector
make docs-serve-versions

# List published versions
make docs-versions

# Commit to gh-pages without pushing; add DOCS_PUSH=true to publish
make docs-deploy-dev
make docs-deploy-release DOCS_VERSION=1.1
```

Versions released before doc versioning existed can be backfilled best-effort. Versions already published are skipped, and nothing is pushed without `--push`:

```bash
scripts/backfill-docs-versions.sh
scripts/backfill-docs-versions.sh --push
```

#### One-time migration from the unversioned site

The `gh-pages` branch predates versioning: it holds one flat site at the branch root, and mike publishes into per-version subdirectories instead. Rather than deleting the leftover root files, rebuild the branch — the old workflow force-pushed an orphan commit on every deploy, so there is no history to keep.

Run this once, after these changes land on `main`:

```bash
S=docs-versioned-migration

# Build every past release, plus dev and the latest alias, on a scratch
# branch. Nothing is pushed, and gh-pages is left untouched.
DOCS_BRANCH=$S scripts/backfill-docs-versions.sh
make docs-deploy-dev DOCS_BRANCH=$S
make docs-deploy-release DOCS_BRANCH=$S DOCS_VERSION=<newest X.Y>

# Review it, then replace gh-pages with it.
git ls-tree --name-only $S
make docs-serve-versions DOCS_BRANCH=$S
git push --force origin $S:gh-pages
```

From then on the two workflows keep the branch current, and the scratch branch can be deleted.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -am 'Add my feature'`)
6. Push to the branch (`git push origin feature/my-feature`)
7. Create a Pull Request

Please see [CONTRIBUTING.md](https://github.com/AllenInstitute/aibs-informatics-core/blob/main/CONTRIBUTING.md) for detailed guidelines.

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings in Google style format
- Keep functions focused and small
- Write tests for new functionality
