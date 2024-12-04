# AIBS Informatics Core

[![Build Status](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml/badge.svg)](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml)

---

## Overview

The AIBS Informatics Core library provides a collection of core functionalities and utilities for various projects at the Allen Institute for Brain Science. This library includes modules for handling environment configurations, data models, executors, and various utility functions.

## Modules

### Utils

The `utils` module provides various utility functions and classes to facilitate common tasks such as logging, hashing, and working with dictionaries and strings.

- **file_operations**: Functions for working with files and directories.
- **decorators**: Decorators for adding functionality to functions and methods.
- **hashing**: Functions for generating hashes.
- **json**: Functions for working with JSON data.
- **logging**: Utilities for setting up and managing logging.
- **modules**: Functions dealing with modules and imports.
- **multiprocessing**: Functions for working with multiprocessing.
- **os_operations**: Functions for working with the operating system.
- **time**: Functions for working with time.
- **units**: Functions for converting units.
- **version**: Functions and classes for handling version numbers.
- **tools.dicttools**: Functions for manipulating dictionaries.
- **tools.strtools**: Functions for manipulating strings.

### Models

The `models` module defines protocols and base models used for serialization and deserialization of data. This module provides base classes for creating data models and utilities for working with data models.

There are a few base classes that can be used to create data models:
- **ModelBase**: A base class for creating data models.
- **DataClassModel**: A base class for creating data models using dataclasses.
- **SchemaModel**: A base class for creating data models using marshmallow schemas + dataclass.
- **WithValidation**: A mixin class for adding validation to data models.


### Executors

The `executors` module provides base classes and utilities for creating and running executors. Executors are responsible for handling specific tasks or requests. They allow for validating inputs/outputs based on schema data models 

- **BaseExecutor**: A base class for creating executors.
- **run_cli_executor**: A utility function for running executors from the command line.

### Env

The `env` module provides a concept of `EnvBase` which allows for creating isolated namespaces based on the type and name of environment:

```python
env_base = EnvBase('dev-projectX')
env_base.prefixed('my_resource', 'blue')  # 'dev-projectX-my_resource-blue'
```


### Collections

The `collections` module provides various collection classes and utilities for working with collections of data.
- Classes
  - **DeepChainMap**: A class for creating recursive capable deep chain maps.
  - **Tree**: A subclass of dict for creating tree structures from sequences.
  - **ValidatedStr**: A class for creating validated strings based on regex patterns.
- Mixins
  - **PostInitMixin**: A mixin class for handling post-initialization tasks.
  - **EnvBaseMixins**: A mixin class for handling environment-related tasks.
- Enums
  - **BaseEnum**: A base class for creating enums.
  - **OrderedEnum**: A base class for creating ordered enums.
  - **StrEnum**: A base class for creating string enums. 
  - **OrderedStrEnum**: A base class for creating ordered string enums.


## Contributing

Any and all PRs are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## Licensing

This software is licensed under the Allen Institute Software License, which is the 2-clause BSD license plus a third clause that prohibits redistribution and use for commercial purposes without further permission. For more information, please visit [Allen Institute Terms of Use](https://alleninstitute.org/terms-of-use/).