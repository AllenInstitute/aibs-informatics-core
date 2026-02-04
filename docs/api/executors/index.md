# Executors

The `executors` module provides base classes and utilities for creating and running executors. Executors are responsible for handling specific tasks or requests with input/output validation based on schema data models.

## Overview

| Module | Description |
|--------|-------------|
| [Base](base.md) | Base executor class for creating task handlers |
| [CLI](cli.md) | Command-line interface utilities for executors |

## Quick Start

```python
from aibs_informatics_core.executors import BaseExecutor

class MyExecutor(BaseExecutor):
    def handle(self, request):
        # Process the request
        return {"result": "success"}
```

## Running from CLI

The library provides a utility function for running executors from the command line:

```python
from aibs_informatics_core.executors import run_cli_executor

# This is typically called as an entry point
run_cli_executor()
```
