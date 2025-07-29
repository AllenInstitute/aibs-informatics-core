__all__ = [
    "BooleanField",
    "CustomAwareDateTime",
    "CustomStringField",
    "DictField",
    "EnumField",
    "FloatField",
    "FrozenSetField",
    "IntegerField",
    "ListField",
    "MappingField",
    "NestedField",
    "PathField",
    "RawField",
    "StringField",
    "TupleField",
    "UnionField",
    "UUIDField",
    "FieldMetadataBuilder",
    "FieldProps",
    "custom_field",
    "field_metadata",
    "ModelProtocol",
    "ModelBase",
    "BaseSchema",
    "DataClassModel",
    "MISSING",
    "NONE",
    "SchemaModel",
    "post_dump",
    "pre_dump",
    "pre_load",
    "validates_schema",
    "PydanticBaseModel",
    "IsoDateTime",
    "IsoDate",
]


import sys
from aibs_informatics_core.models.base.custom_fields import (
    BooleanField,
    CustomAwareDateTime,
    CustomStringField,
    DictField,
    EnumField,
    FloatField,
    FrozenSetField,
    IntegerField,
    ListField,
    MappingField,
    NestedField,
    PathField,
    RawField,
    StringField,
    TupleField,
    UnionField,
    UUIDField,
)
from aibs_informatics_core.models.base.field_utils import (
    FieldMetadataBuilder,
    FieldProps,
    custom_field,
    field_metadata,
)
from aibs_informatics_core.models.base.model import (
    MISSING,
    NONE,
    BaseSchema,
    DataClassModel,
    ModelBase,
    ModelProtocol,
    SchemaModel,
    post_dump,
    pre_dump,
    pre_load,
    validates_schema,
)

try:
    from aibs_informatics_core.models.base._pydantic_model import PydanticBaseModel
    from aibs_informatics_core.models.base._pydantic_fields import (
        IsoDateTime,
        IsoDate,
    )
except (ImportError, ModuleNotFoundError):
    import types

    class _MissingPydantic(types.ModuleType):
        """Stub that raises a helpful error when any attribute is accessed."""

        __all__ = ()

        def __getattr__(self, item):
            raise ImportError(
                "Optional dependency 'pydantic' is required for "
                "`aibs_informatics_core.models.base.PydanticBaseModel`. "
                "Install it with: pip install 'aibs-informatics-core[pydantic]'"
            )

    # Ensure subsequent `import pydantic` resolves to the stub so recursive
    # import attempts don’t continually re‑raise a generic ModuleNotFoundError.
    sys.modules.setdefault("pydantic", _MissingPydantic("pydantic"))
