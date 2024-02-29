#!/usr/bin/env python3
import json
import subprocess

# Import the version directly if it's part of your package's namespace
# from my_package.version import __version__ as current_version


def get_version_from_file(file_path: str) -> str:
    """Extract version from a Python file."""
    version = {}
    with open(file_path) as file:
        exec(file.read(), version)
    return version["__version__"]


def get_last_version() -> str:
    """Return the version number of the last release."""
    json_string = (
        subprocess.run(
            ["gh", "release", "view", "--json", "tagName"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        .stdout.decode("utf8")
        .strip()
    )
    return json.loads(json_string)["tagName"]


def bump_patch_number(version_number: str) -> str:
    """Return a copy of `version_number` with the patch number incremented."""
    major, minor, patch = version_number.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def create_new_patch_release():
    """Create a new patch release on GitHub."""
    try:
        current_version = get_version_from_file("path/to/your/version.py")
    except subprocess.CalledProcessError as err:
        raise
    else:
        new_version_number = bump_patch_number(current_version)

    subprocess.run(
        ["gh", "release", "create", "--generate-notes", new_version_number],
        check=True,
    )


# def create_new_patch_release():
#     """Create a new patch release on GitHub."""
#     try:
#         last_version_number = get_last_version()
#     except subprocess.CalledProcessError as err:
#         if err.stderr.decode("utf8").startswith("HTTP 404:"):
#             # The project doesn't have any releases yet.
#             new_version_number = "0.0.1"
#         else:
#             raise
#     else:
#         new_version_number = bump_patch_number(last_version_number)

#     subprocess.run(
#         ["gh", "release", "create", "--generate-notes", new_version_number],
#         check=True,
#     )


if __name__ == "__main__":
    create_new_patch_release()
