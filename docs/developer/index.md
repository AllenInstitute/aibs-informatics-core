# Developer Guide

This guide provides information for developers who want to contribute to the AIBS Informatics Core library.

## Development Setup

### Prerequisites

- Python 3.9 or higher
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
