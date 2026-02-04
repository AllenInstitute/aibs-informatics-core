# Env

Environment configuration and namespace management.

## Overview

The `env` module provides the `EnvBase` class which allows for creating isolated namespaces based on the type and name of environment.

## Usage

```python
from aibs_informatics_core.env import EnvBase

env_base = EnvBase('dev-projectX')
env_base.prefixed('my_resource', 'blue')  # 'dev-projectX-my_resource-blue'
```

---

::: aibs_informatics_core.env
