# AIBS Informatics Core

[![Build Status](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml/badge.svg)](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/AllenInstitute/aibs-informatics-core/graph/badge.svg?token=X66KBYWELP)](https://codecov.io/gh/AllenInstitute/aibs-informatics-core)

---

## Overview

The AIBS Informatics Core library provides a collection of core functionalities and utilities for various projects at the Allen Institute for Brain Science. This library includes modules for handling environment configurations, data models, executors, and various utility functions.

## Features

- **Collections** - Specialized collection classes including `DeepChainMap`, `Tree`, `ValidatedStr`, and various enum base classes
- **Environment** - `EnvBase` for creating isolated namespaces based on environment type and name
- **Models** - Base classes for data serialization/deserialization using dataclasses and marshmallow schemas
- **Executors** - Base classes for creating and running task executors with input/output validation
- **Utils** - Comprehensive utility functions for file operations, logging, hashing, JSON handling, and more

## Quick Start

### Installation

```bash
pip install aibs-informatics-core
```

### Basic Usage

```python
from aibs_informatics_core.env import EnvBase

# Create an environment namespace
env_base = EnvBase('dev-projectX')
env_base.prefixed('my_resource', 'blue')  # 'dev-projectX-my_resource-blue'
```

## Modules

| Module | Description |
|--------|-------------|
| [Collections](api/collections.md) | Collection classes and utilities (DeepChainMap, Tree, ValidatedStr, enums) |
| [Env](api/env.md) | Environment configuration and namespace management |
| [Executors](api/executors/index.md) | Base executor classes and CLI utilities |
| [Models](api/models/index.md) | Data model base classes and serialization protocols |
| [Utils](api/utils/index.md) | Utility functions for file operations, logging, hashing, and more |

## Contributing

Any and all PRs are welcome. Please see [CONTRIBUTING.md](https://github.com/AllenInstitute/aibs-informatics-core/blob/main/CONTRIBUTING.md) for more information.

## License

This software is licensed under the Allen Institute Software License, which is the 2-clause BSD license plus a third clause that prohibits redistribution and use for commercial purposes without further permission. For more information, please visit [Allen Institute Terms of Use](https://alleninstitute.org/terms-of-use/).
