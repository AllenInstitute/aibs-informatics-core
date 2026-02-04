# Models

The `models` module defines protocols and base models used for serialization and deserialization of data.

## Overview

| Module | Description |
|--------|-------------|
| [Base](base.md) | Base model classes (`ModelBase`, `DataClassModel`, `SchemaModel`) |
| [Status](status.md) | Status-related models |
| [Unique IDs](unique-ids.md) | Unique identifier models |
| [Version](version.md) | Version handling models |
| [Data Sync](data-sync.md) | Data synchronization models |
| [Email Address](email-address.md) | Email address models |

## Base Classes

There are a few base classes that can be used to create data models:

- **ModelBase**: A base class for creating data models
- **DataClassModel**: A base class for creating data models using dataclasses
- **SchemaModel**: A base class for creating data models using marshmallow schemas + dataclass
- **WithValidation**: A mixin class for adding validation to data models

## Quick Start

```python
from dataclasses import dataclass
from aibs_informatics_core.models import SchemaModel

@dataclass
class MyModel(SchemaModel):
    name: str
    value: int

# Serialize
model = MyModel(name="test", value=42)
json_str = model.to_json()

# Deserialize
restored = MyModel.from_json(json_str)
```
