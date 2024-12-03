# AIBS Informatics Core

[![Build Status](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml/badge.svg)](https://github.com/AllenInstitute/aibs-informatics-core/actions/workflows/build.yml)

---

Core library to be used as foundation across multiple projects 


### Versioning

This project uses [semantic versioning](https://semver.org/). The version is stored in the `_version.py` file. 

This version is updated automatically via GitHub actions which use commit messages and PR titles to determine the version bump. The following keywords in a commit message will trigger a version bump:
  - `(PATCH)` - for bug fixes, documentation updates, and small changes
  - `(MINOR)` - for new features
  - `(MAJOR)` - for breaking changes.

Notes about versioning using the above keywords:
  - The keyword must be in all caps and surrounded by parentheses
  - The If you specify multiple keywords in a single commit message, the highest version bump will be used
  - If you specify `(NONE)` keyword in a commit message, the version will not be bumped regardless of other keywords in the commit message.

## Contributing

Any and all PRs are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## Licensing

This software is licensed under the Allen Institute Software License, which is the 2-clause BSD license plus a third clause that prohibits redistribution and use for commercial purposes without further permission. For more information, please visit [Allen Institute Terms of Use](https://alleninstitute.org/terms-of-use/).