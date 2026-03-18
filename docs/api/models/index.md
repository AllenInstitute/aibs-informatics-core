# Models

The `models` module defines protocols and base models used for serialization and deserialization of data.

## Overview

| Module | Description |
|--------|-------------|
| [Base](base.md) | Base model classes (`ModelProtocol`, `ModelBase`, `PydanticBaseModel`) |
| [Status](status.md) | Status-related models |
| [Unique IDs](unique-ids.md) | Unique identifier models |
| [Version](version.md) | Version handling models |
| [Data Sync](data-sync.md) | Data synchronization models |
| [Email Address](email-address.md) | Email address models |

## Base Classes

There are a few base classes that can be used to create data models:

- **ModelProtocol**: A runtime-checkable protocol defining the serialization/deserialization interface
- **ModelBase**: An abstract base class implementing the serialization protocol
- **PydanticBaseModel**: The primary base class for creating data models (backed by Pydantic)
- **IsoDateTime / IsoDate**: Annotated Pydantic types for ISO 8601 datetime and date fields

## Quick Start

```python
from aibs_informatics_core.models.base import PydanticBaseModel

class MyModel(PydanticBaseModel):
    name: str
    value: int

# Serialize
model = MyModel(name="test", value=42)
json_str = model.to_json()

# Deserialize
restored = MyModel.from_json(json_str)
```
