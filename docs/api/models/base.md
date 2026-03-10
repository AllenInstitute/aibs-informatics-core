# Base Models

Base model classes for data serialization and deserialization.

## Classes

### ModelProtocol

A runtime-checkable protocol defining the serialization/deserialization interface (`from_dict`, `to_dict`, `from_json`, `to_json`, `from_path`, `to_path`).

### ModelBase

An abstract base class implementing common serialization methods (JSON, YAML, file I/O).

### PydanticBaseModel

The primary base class for creating data models, backed by Pydantic with automatic camelCase alias support.

### IsoDateTime / IsoDate

Annotated Pydantic types for ISO 8601 datetime and date fields with custom parsing and serialization.

---

::: aibs_informatics_core.models.base
