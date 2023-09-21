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
from typing import Literal, Optional, Tuple, Union

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
    DEV = "dev"
    INFRA = "infra"
    PROD = "prod"
    TEST = "test"


SupportedDelim = Literal["-", "_", ":", "/"]


class EnvBase(ValidatedStr):

    ENV_BASE_KEY = ENV_BASE_KEY
    ENV_LABEL_KEY = ENV_LABEL_KEY
    ENV_TYPE_KEY = ENV_TYPE_KEY
    regex_pattern = re.compile(f"({'|'.join(EnvType.values())})" r"(?:-(\w+)|)")

    @property
    def env_type(self) -> EnvType:
        return self.to_type_and_label()[0]

    @property
    def env_label(self) -> Optional[str]:
        return self.to_type_and_label()[1]

    def get_construct_id(self, *names: str) -> str:
        return self.prefixed(*names)

    def get_stack_name(self, *names: str) -> str:
        return self.prefixed(*names)

    def get_stage_name(self, *names: str) -> str:
        return self.prefixed(*names)

    def get_pipeline_name(self, *names: str) -> str:
        return self.prefixed(*names)

    def get_repository_name(self, *names: str) -> str:
        return self.concat(self, self.concat(*names), delim="/")

    def get_resource_name(self, *names: str) -> str:
        return self.prefixed(*names)

    def get_table_name(self, name: str) -> str:
        return self.prefixed(name)

    def get_function_name(self, name: str) -> str:
        return self.prefixed(name)

    def get_state_machine_name(self, name: str) -> str:
        return self.get_resource_name(name)

    def get_job_name(self, name: str, hash_value: str) -> str:
        return self.get_resource_name(name, hash_value)

    def get_state_machine_log_group_name(self, name: str) -> str:
        return self.concat(
            # https://docs.aws.amazon.com/step-functions/latest/dg/bp-cwl.html
            "/aws/vendedlogs",
            self,
            "states",
            name,
            delim="/",
        )

    def get_metric_namespace(self, name: str) -> str:
        return self.concat("AIBS", self, name, delim="/")

    def get_bucket_name(self, base_name: str, account_id: str, region: str) -> str:
        return self.concat(self, base_name, region, account_id, delim="-")

    def get_ssm_param_name(self, *names: str) -> str:
        return self.concat("", self, self.concat(*names), delim="/")

    def prefixed(self, *names: str, delim: SupportedDelim = "-") -> str:
        """Returns as <env_base>-<name1>-<name2>..."""
        # Don't add if self in names already
        if names and (names[0] == self or names[0].startswith(self + delim)):
            return self.concat(*names, delim=delim)
        return self.concat(self, *names, delim=delim)

    def suffixed(self, *names: str, delim: SupportedDelim = "-") -> str:
        """Returns as <name1>-...<nameN>-<env_base>"""
        # Don't add if self in names already
        if names and (names[-1] == self or names[-1].endswith(delim + self)):
            return self.concat(*names, delim=delim)
        return self.concat(*names, self, delim=delim)

    @classmethod
    def concat(cls, *names: str, delim: SupportedDelim = "-") -> str:
        return delim.join(names)

    def to_env(self):
        """Write as environnment variable"""
        set_env_var(ENV_BASE_KEY, self)

    def to_type_and_label(self) -> Tuple[EnvType, Optional[str]]:
        env_type, env_label = self.get_match_groups()
        return (EnvType(env_type), env_label)

    @classmethod
    def from_type_and_label(cls, env_type: EnvType, env_label: Optional[str] = None) -> "EnvBase":
        """Returns <env_name>[-<env_label>]"""
        return EnvBase(f"{env_type.value}-{env_label}" if env_label else env_type.value)

    @classmethod
    def from_env(cls) -> "EnvBase":
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
            return EnvBase(env_base)
        else:
            try:
                env_type = cls.load_env_type__from_env()
                env_label = cls.load_env_label__from_env()
            except:
                raise ApplicationException("Could not resolve Env Base or Env Type from env")

            env_base = cls.from_type_and_label(EnvType(env_type), env_label=env_label)
            return env_base

    @classmethod
    def load_env_type__from_env(cls) -> EnvType:
        env_type = get_env_var(ENV_TYPE_KEY, ENV_TYPE_KEY_ALIAS)
        if not env_type:
            raise ApplicationException(
                f"{cls} is not found as {ENV_TYPE_KEY} or {ENV_TYPE_KEY_ALIAS}"
            )
        return EnvType(env_type)

    @classmethod
    def load_env_label__from_env(cls) -> str:
        return get_env_var(ENV_LABEL_KEY, ENV_LABEL_KEY_ALIAS, LABEL_KEY, LABEL_KEY_ALIAS)


class EnvBaseMixins:
    @property
    def env_base(self) -> EnvBase:
        """returns env base

        If env base has not been set, it sets the value using environment variables

        Returns:
            EnvBase: env base
        """
        try:
            return self._env_base
        except AttributeError:
            self.env_base = None
            return self._env_base

    @env_base.setter
    def env_base(self, env_base: Optional[EnvBase] = None):
        """Sets env base

        If None is provided, env variables are read to infer env base

        Args:
            env_base (Optional[EnvBase], optional): environment base to use. Defaults to None.
        """
        self._env_base = get_env_base(env_base)


class EnvBaseEnumMixins:
    def prefix_with(self, env_base: EnvBase = None) -> str:
        env_base = get_env_base(env_base)
        if isinstance(self, Enum):
            return env_base.prefixed(self.value)
        else:
            return env_base.prefixed(str(self))


class ResourceNameBaseEnum(str, EnvBaseEnumMixins, Enum):
    def __str__(self) -> str:
        return self.value

    def get_name(self, env_base: EnvBase) -> str:
        return self.prefix_with(env_base)


def get_env_base(env_base: Optional[Union[str, EnvBase]] = None) -> EnvBase:
    """Will look for the env_base as an environment variable."""
    if env_base:
        return env_base if isinstance(env_base, EnvBase) else EnvBase(env_base)
    return EnvBase.from_env()


def get_env_type(
    env_type: Optional[Union[str, EnvType]] = None, default_env_type: Optional[EnvType] = None
) -> EnvType:
    """Loads EnvType from environment or normalizes input

    Note that if loading from environment, EnvBase variable takes precedence over EnvType

    """
    if env_type:
        return env_type if isinstance(env_type, EnvType) else EnvType(env_type)
    try:
        return EnvBase.from_env().env_type
    except Exception as e:
        if default_env_type:
            return default_env_type
        raise e


class _Missing:
    pass


MISSING = _Missing()


def get_env_label(env_label: Union[Optional[str], _Missing] = MISSING) -> Optional[str]:
    """Get Environment label

    If not specified, it will be loaded from envirionment (First checking for env base, then label)

    Args:
        env_label (Union[Optional[str], _Missing], optional): env label. Defaults to MISSING.

    Returns:
        Optional[str]: env label string
    """
    if isinstance(env_label, _Missing):
        try:
            # First check if EnvBase exists and
            return EnvBase.from_env().env_label
        except:
            # next check for env label.
            return EnvBase.load_env_label__from_env()
    # Right now env label regex is only baked into EnvBase, so let's
    # create an EnvBase to validate
    return EnvBase.from_type_and_label(EnvType.DEV, env_label=env_label).env_label
