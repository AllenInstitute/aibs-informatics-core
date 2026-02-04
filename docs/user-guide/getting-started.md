# Getting Started

This guide will help you get started with the AIBS Informatics Core library.

## Installation

### Using pip

```bash
pip install aibs-informatics-core
```

### Using uv

```bash
uv add aibs-informatics-core
```

### Optional Dependencies

For Pydantic support:

```bash
pip install aibs-informatics-core[pydantic]
```

## Basic Concepts

### Environment Namespacing

The `EnvBase` class provides a way to create isolated namespaces for your resources:

```python
from aibs_informatics_core.env import EnvBase

# Create an environment namespace
env = EnvBase('dev-myproject')

# Generate prefixed resource names
resource_name = env.prefixed('my_resource', 'blue')
print(resource_name)  # 'dev-myproject-my_resource-blue'
```

### Data Models

Create type-safe data models using the provided base classes:

```python
from dataclasses import dataclass
from aibs_informatics_core.models import SchemaModel

@dataclass
class MyModel(SchemaModel):
    name: str
    value: int

# Serialize/deserialize
model = MyModel(name="test", value=42)
json_str = model.to_json()
restored = MyModel.from_json(json_str)
```

### Executors

Create task executors with automatic input/output validation:

```python
from aibs_informatics_core.executors import BaseExecutor

class MyExecutor(BaseExecutor):
    def handle(self, request):
        # Process the request
        return {"result": "success"}
```

## Next Steps

- Explore the [API Reference](../api/index.md) for detailed documentation
- Check the [Configuration Guide](configuration.md) for advanced setup options
- See the [Developer Guide](../developer/index.md) for contribution guidelines
