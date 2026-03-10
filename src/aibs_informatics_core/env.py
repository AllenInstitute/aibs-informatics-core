__all__ = [
    "ENV_BASE_KEY",
    "ENV_BASE_KEY_ALIAS",
    "ENV_LABEL_KEY",
    "ENV_LABEL_KEY_ALIAS",
    "ENV_TYPE_KEY",
    "ENV_TYPE_KEY_ALIAS",
    "LABEL_KEY",
    "LABEL_KEY_ALIAS",
    "EnvBase",
    "EnvBaseEnumMixins",
    "EnvBaseMixins",
    "EnvType",
    "ResourceNameBaseEnum",
    "SupportedDelim",
    "get_env_base",
    "get_env_type",
    "get_env_label",
]

import re
from enum import Enum
from typing import Generic, Literal, TypeVar, overload

from aibs_informatics_core.collections import StrEnum, ValidatedStr
from aibs_informatics_core.exceptions import ApplicationException
from aibs_informatics_core.utils.os_operations import get_env_var, set_env_var

ENV_BASE_KEY = "env_base"
ENV_LABEL_KEY = "env_label"
ENV_TYPE_KEY = "env_type"
LABEL_KEY = "label"

ENV_BASE_KEY_ALIAS = ENV_BASE_KEY.upper()
ENV_LABEL_KEY_ALIAS = ENV_LABEL_KEY.upper()
ENV_TYPE_KEY_ALIAS = ENV_TYPE_KEY.upper()
LABEL_KEY_ALIAS = LABEL_KEY.upper()


class EnvType(StrEnum):
    """Enumeration of supported environment types."""

    DEV = "dev"
    TEST = "test"
    PROD = "prod"


SupportedDelim = Literal["-", "_", ":", "/"]
E = TypeVar("E", bound="EnvBase")


class EnvBase(ValidatedStr):
    """Environment namespace for generating prefixed resource names.

    Parses an environment string (e.g. ``"dev-myproject"``) into an environment
    type and optional label. Provides methods to generate consistently prefixed
    names for AWS resources such as stacks, tables, functions, and buckets.
    """

    ENV_BASE_KEY = ENV_BASE_KEY
    ENV_LABEL_KEY = ENV_LABEL_KEY
    ENV_TYPE_KEY = ENV_TYPE_KEY
    regex_pattern = re.compile(f"({'|'.join(EnvType.values())})" r"(?:-(\w+)|)")

    @property
    def env_type(self) -> EnvType:
        """The environment type (dev, test, or prod)."""
        return self.to_type_and_label()[0]

    @property
    def env_label(self) -> str | None:
        """The environment label, or None if not specified."""
        return self.to_type_and_label()[1]

    def get_construct_id(self, *names: str) -> str:
        """Generate a CDK construct ID with the env base prefix.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Prefixed construct ID string.
        """
        return self.prefixed(*names)

    def get_stack_name(self, *names: str) -> str:
        """Generate a CloudFormation stack name with the env base prefix.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Prefixed stack name string.
        """
        return self.prefixed(*names)

    def get_stage_name(self, *names: str) -> str:
        """Generate a pipeline stage name with the env base prefix.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Prefixed stage name string.
        """
        return self.prefixed(*names)

    def get_pipeline_name(self, *names: str) -> str:
        """Generate a pipeline name with the env base prefix.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Prefixed pipeline name string.
        """
        return self.prefixed(*names)

    def get_repository_name(self, *names: str) -> str:
        """Generate a repository name using ``/`` as delimiter.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Repository name in the form ``<env_base>/<name1>/<name2>/...``.
        """
        return self.concat(self, self.concat(*names), delim="/")

    def get_resource_name(self, *names: str) -> str:
        """Generate a generic resource name with the env base prefix.

        Args:
            *names: Name parts to join after the prefix.

        Returns:
            Prefixed resource name string.
        """
        return self.prefixed(*names)

    def get_table_name(self, name: str) -> str:
        """Generate a DynamoDB table name with the env base prefix.

        Args:
            name: Table base name.

        Returns:
            Prefixed table name string.
        """
        return self.prefixed(name)

    def get_function_name(self, name: str) -> str:
        """Generate a Lambda function name with the env base prefix.

        Args:
            name: Function base name.

        Returns:
            Prefixed function name string.
        """
        return self.prefixed(name)

    def get_state_machine_name(self, name: str) -> str:
        """Generate a Step Functions state machine name with the env base prefix.

        Args:
            name: State machine base name.

        Returns:
            Prefixed state machine name string.
        """
        return self.get_resource_name(name)

    def get_job_name(self, name: str, hash_value: str) -> str:
        """Generate a Batch job name with the env base prefix.

        Args:
            name: Job base name.
            hash_value: Hash value to append for uniqueness.

        Returns:
            Prefixed job name string.
        """
        return self.get_resource_name(name, hash_value)

    def get_state_machine_log_group_name(self, name: str) -> str:
        """Generate a CloudWatch log group name for a Step Functions state machine.

        Args:
            name: State machine base name.

        Returns:
            Log group name in the format ``/aws/vendedlogs/<env_base>/states/<name>``.
        """
        return self.concat(
            # https://docs.aws.amazon.com/step-functions/latest/dg/bp-cwl.html
            "/aws/vendedlogs",
            self,
            "states",
            name,
            delim="/",
        )

    def get_metric_namespace(self, name: str) -> str:
        """Generate a CloudWatch metric namespace.

        Args:
            name: Metric namespace base name.

        Returns:
            Metric namespace in the form ``AIBS/<env_base>/<name>``.
        """
        return self.concat("AIBS", self, name, delim="/")

    def get_bucket_name(self, base_name: str, account_id: str, region: str) -> str:
        """Generate an S3 bucket name.

        Args:
            base_name: Bucket base name.
            account_id: AWS account ID.
            region: AWS region.

        Returns:
            Bucket name in the form ``<env_base>-<base_name>-<region>-<account_id>``.
        """
        return self.concat(self, base_name, region, account_id, delim="-")

    def get_ssm_param_name(self, *names: str) -> str:
        """Generate an SSM parameter name.

        Args:
            *names: Parameter name parts.

        Returns:
            SSM parameter name in the form ``/<env_base>/<name1>/<name2>/...``.
        """
        return self.concat("", self, self.concat(*names), delim="/")

    def prefixed(self, *names: str, delim: SupportedDelim = "-") -> str:
        """Return a string with the env base as prefix.

        Args:
            *names: Name parts to join after the prefix.
            delim: Delimiter between parts.

        Returns:
            String in the form ``<env_base><delim><name1><delim>...``.
        """
        # Don't add if self in names already
        if names and (names[0] == self or names[0].startswith(self + delim)):
            return self.concat(*names, delim=delim)
        return self.concat(self, *names, delim=delim)

    def suffixed(self, *names: str, delim: SupportedDelim = "-") -> str:
        """Return a string with the env base as suffix.

        Args:
            *names: Name parts to join before the suffix.
            delim: Delimiter between parts.

        Returns:
            String in the form ``<name1><delim>...<nameN><delim><env_base>``.
        """
        # Don't add if self in names already
        if names and (names[-1] == self or names[-1].endswith(delim + self)):
            return self.concat(*names, delim=delim)
        return self.concat(*names, self, delim=delim)

    @classmethod
    def concat(cls, *names: str, delim: SupportedDelim = "-") -> str:
        """Join name parts with a delimiter.

        Args:
            *names: Name parts to concatenate.
            delim: Delimiter between parts.

        Returns:
            Concatenated string.
        """
        return delim.join(names)

    def to_env(self):
        """Write the env base value to the ``env_base`` environment variable."""
        set_env_var(ENV_BASE_KEY, self)

    def to_type_and_label(self) -> tuple[EnvType, str | None]:
        """Parse into environment type and optional label.

        Returns:
            A tuple of ``(EnvType, label)`` where label may be None.
        """
        env_type, env_label = self.get_match_groups()
        return (EnvType(env_type), env_label)

    @classmethod
    def from_type_and_label(cls: type[E], env_type: EnvType, env_label: str | None = None) -> E:
        """Construct an EnvBase from an environment type and optional label.

        Args:
            env_type: The environment type.
            env_label: Optional label to append after the type.

        Returns:
            A new EnvBase instance in the form ``<env_type>[-<env_label>]``.
        """
        return cls(f"{env_type.value}-{env_label}" if env_label else env_type.value)

    @classmethod
    def from_env(cls: type[E]) -> E:
        """Get value from environment variables

        1. Checks for env base variables.
        2. Checks for env type and label:

        Environment Variable Keys:
        env base  : "env_base" / "ENV_BASE"
        env type  : "env_type" / "ENV_TYPE"
        env label : "env_label" / "ENV_LABEL" / "label" / "LABEL"
        Raises:
            ApplicationException: if variables are not found.

        Returns:
            EnvBase
        """
        env_base = get_env_var(ENV_BASE_KEY, ENV_BASE_KEY_ALIAS)
        if env_base:
            return cls(env_base)
        else:
            try:
                env_type = cls.load_env_type__from_env()
                env_label = cls.load_env_label__from_env()
            except Exception:
                raise ApplicationException("Could not resolve Env Base or Env Type from env")

            env_base = cls.from_type_and_label(EnvType(env_type), env_label=env_label)
            return env_base

    @classmethod
    def load_env_type__from_env(cls) -> EnvType:
        """Load the environment type from environment variables.

        Checks ``env_type`` and ``ENV_TYPE`` environment variables.

        Returns:
            The resolved EnvType.

        Raises:
            ApplicationException: If no environment type variable is found.
        """
        env_type = get_env_var(ENV_TYPE_KEY, ENV_TYPE_KEY_ALIAS)
        if not env_type:
            raise ApplicationException(
                f"{cls} is not found as {ENV_TYPE_KEY} or {ENV_TYPE_KEY_ALIAS}"
            )
        return EnvType(env_type)

    @classmethod
    def load_env_label__from_env(cls) -> str | None:
        """Load the environment label from environment variables.

        Checks ``env_label``, ``ENV_LABEL``, ``label``, and ``LABEL``
        environment variables.

        Returns:
            The label string, or None if not set.
        """
        return get_env_var(ENV_LABEL_KEY, ENV_LABEL_KEY_ALIAS, LABEL_KEY, LABEL_KEY_ALIAS)


class EnvBaseMixinsBase(Generic[E]):
    """Generic mixin providing ``env_base`` property with lazy environment loading."""

    @property
    def env_base(self) -> E:
        """returns env base

        If env base has not been set, it sets the value using environment variables

        Returns:
            env base
        """
        try:
            return self._env_base
        except AttributeError:
            self.env_base = None  # type: ignore[assignment]
            return self._env_base

    @env_base.setter
    def env_base(self, env_base: E | None = None):
        """Sets env base

        If None is provided, env variables are read to infer env base

        Args:
            env_base (Optional[EnvBase], optional): environment base to use. Defaults to None.
        """
        self._env_base = get_env_base(env_base, env_base_class=self._env_base_class())

    @classmethod
    def _env_base_class(cls) -> type[E]:
        return cls.__orig_bases__[0].__args__[0]  # type: ignore


# ----------------------------------
#        Mixins & Enums
# ----------------------------------


class EnvBaseMixins(EnvBaseMixinsBase[EnvBase]):
    """Concrete mixin providing ``env_base`` property bound to ``EnvBase``."""

    @classmethod
    def _env_base_class(cls) -> type[EnvBase]:
        return EnvBase


class EnvBaseEnumMixins:
    """Mixin for enums that provides environment-prefixed name generation."""

    def prefix_with(self, env_base: E | None = None, env_base_class: type[E] | None = None) -> str:
        """Prefix the enum value with an environment base.

        Args:
            env_base: Optional EnvBase instance to use.
            env_base_class: Optional EnvBase subclass for loading from environment.

        Returns:
            The prefixed string.
        """
        env_base_ = get_env_base(env_base, env_base_class)
        if isinstance(self, Enum):
            return env_base_.prefixed(self.value)
        else:
            return env_base_.prefixed(str(self))


class ResourceNameBaseEnum(str, EnvBaseEnumMixins, Enum):
    """Enum for defining resource names that can be prefixed with an environment base."""

    def __str__(self) -> str:
        return self.value

    def get_name(self, env_base: EnvBase) -> str:
        """Get the environment-prefixed resource name.

        Args:
            env_base: The environment base to use as prefix.

        Returns:
            The prefixed resource name string.
        """
        return self.prefix_with(env_base)


# ----------------------------------
#        getter functions
# ----------------------------------


@overload
def get_env_base() -> EnvBase: ...


@overload
def get_env_base(env_base: str | EnvBase) -> EnvBase: ...


@overload
def get_env_base(env_base: Literal[None]) -> EnvBase: ...


@overload
def get_env_base(env_base: Literal[None], env_base_class: Literal[None]) -> EnvBase: ...


@overload
def get_env_base(env_base: Literal[None], env_base_class: type[E]) -> E: ...


@overload
def get_env_base(env_base: str | E, env_base_class: type[E]) -> E: ...


@overload
def get_env_base(env_base: str | E, env_base_class: Literal[None]) -> EnvBase: ...


def get_env_base(
    env_base: str | E | None = None,
    env_base_class: type[E | EnvBase] | None = None,
) -> E | EnvBase:
    """Resolve an EnvBase, loading from environment if not provided.

    Args:
        env_base: An existing env base string/instance, or None to load from environment.
        env_base_class: The EnvBase subclass to use for construction. Defaults to EnvBase.

    Returns:
        The resolved EnvBase instance.
    """
    env_base_cls: type[E] = env_base_class or EnvBase  # type: ignore[assignment]
    if env_base:
        if isinstance(env_base, env_base_cls):
            return env_base
        else:
            return env_base_cls(env_base)
    return env_base_cls.from_env()


def get_env_type(
    env_type: str | EnvType | None = None,
    default_env_type: EnvType | None = None,
    env_base_class: E | None = None,
) -> EnvType:
    """Resolve an EnvType, loading from environment if not provided.

    If loading from environment, the ``EnvBase`` variable takes precedence
    over the ``EnvType`` variable.

    Args:
        env_type: An existing env type string/instance, or None to load from environment.
        default_env_type: Fallback EnvType if loading from environment fails.
        env_base_class: Optional EnvBase subclass for environment resolution.

    Returns:
        The resolved EnvType.

    Raises:
        Exception: If no env type can be resolved and no default is provided.
    """
    if env_type:
        return env_type if isinstance(env_type, EnvType) else EnvType(env_type)
    try:
        return (env_base_class or EnvBase).from_env().env_type
    except Exception as e:
        if default_env_type:
            return default_env_type
        raise e


class _Missing:
    pass


MISSING = _Missing()


def get_env_label(
    env_label: str | None | _Missing = MISSING,
    env_base_class: E | None = None,
) -> str | None:
    """Get Environment label

    If not specified, it will be loaded from envirionment (First checking for env base, then label)

    Args:
        env_label (Union[Optional[str], _Missing], optional): env label. Defaults to MISSING.

    Returns:
        env label string if exists, else None
    """
    env_base_cls = env_base_class or EnvBase
    if isinstance(env_label, _Missing):
        try:
            # First check if EnvBase exists and
            return env_base_cls.from_env().env_label
        except Exception:
            # next check for env label.
            return env_base_cls.load_env_label__from_env()
    # Right now env label regex is only baked into EnvBase, so let's
    # create an EnvBase to validate
    return env_base_cls.from_type_and_label(EnvType.DEV, env_label=env_label).env_label
