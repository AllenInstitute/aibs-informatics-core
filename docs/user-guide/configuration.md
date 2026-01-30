# Configuration

This guide covers configuration options for the AIBS Informatics Core library.

## Environment Variables

The library uses environment variables for certain configurations. Here are the commonly used ones:

### Logging Configuration

You can configure logging behavior using the logging utilities:

```python
from aibs_informatics_core.utils.logging import get_logger, setup_logging

# Set up logging with default configuration
setup_logging()

# Get a logger for your module
logger = get_logger(__name__)
logger.info("Application started")
```

## EnvBase Configuration

The `EnvBase` class can be configured with different environment types and names:

```python
from aibs_informatics_core.env import EnvBase

# Development environment
dev_env = EnvBase('dev-projectX')

# Production environment
prod_env = EnvBase('prod-projectX')

# Create prefixed names for resources
dev_env.prefixed('bucket', 'data')  # 'dev-projectX-bucket-data'
prod_env.prefixed('bucket', 'data')  # 'prod-projectX-bucket-data'
```

## Model Serialization

### JSON Serialization

Data models support JSON serialization out of the box:

```python
from dataclasses import dataclass
from aibs_informatics_core.models import SchemaModel

@dataclass
class Config(SchemaModel):
    debug: bool = False
    max_retries: int = 3

config = Config(debug=True)
json_data = config.to_json()
```

### Custom Field Types

The library provides custom fields for common use cases:

```python
from aibs_informatics_core.models.base.custom_fields import PathField
```

## Executor Configuration

Executors can be configured with validation schemas:

```python
from aibs_informatics_core.executors import BaseExecutor

class ConfigurableExecutor(BaseExecutor):
    # Define request/response schemas for validation
    pass
```

## Advanced Configuration

### Validation

Use the `WithValidation` mixin to add validation to your models:

```python
from dataclasses import dataclass
from aibs_informatics_core.models import SchemaModel
from aibs_informatics_core.collections import PostInitMixin

@dataclass
class ValidatedConfig(SchemaModel, PostInitMixin):
    port: int
    
    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
```
