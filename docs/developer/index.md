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

Using uv (recommended):

```bash
uv sync --group dev
```

Using pip:

```bash
pip install -e ".[dev]"
```

## Project Structure

```
aibs-informatics-core/
├── src/
│   └── aibs_informatics_core/
│       ├── collections.py      # Collection classes and utilities
│       ├── env.py              # Environment configuration
│       ├── exceptions.py       # Custom exceptions
│       ├── executors/          # Executor base classes
│       ├── models/             # Data model base classes
│       └── utils/              # Utility functions
├── test/                       # Test files
├── docs/                       # Documentation
├── pyproject.toml              # Project configuration
└── Makefile                    # Build automation
```

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run specific test file
pytest test/aibs_informatics_core/test_collections.py
```

## Code Quality

### Linting

```bash
# Run ruff linter
make lint

# Auto-fix linting issues
make lint-fix
```

### Type Checking

```bash
# Run mypy type checker
make type-check
```

## Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
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
