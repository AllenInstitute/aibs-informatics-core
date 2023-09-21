from typing import Optional

from aibs_informatics_test_resources import BaseTest as _BaseTest
from aibs_informatics_test_resources import does_not_raise
from aibs_informatics_test_resources import reset_environ_after_test as reset_environ_after_test

from aibs_informatics_core.env import ENV_BASE_KEY, EnvBase, EnvType


class BaseTest(_BaseTest):
    @property
    def env_base(self) -> EnvBase:
        if not hasattr(self, "_env_base"):
            self._env_base = EnvBase.from_type_and_label(EnvType.DEV, "marmotdev")
        return self._env_base

    @env_base.setter
    def env_base(self, env_base: EnvBase):
        self._env_base = env_base

    def set_env_base_env_var(self, env_base: Optional[EnvBase] = None):
        self.set_env_vars((ENV_BASE_KEY, env_base or self.env_base))
