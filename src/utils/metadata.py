"""Utilities for reading evaluation metadata from eval.yaml files."""

from importlib import resources
from typing import Any

import yaml


def load_version_from_yaml(package: str) -> str:
    """Load the version string from an eval's eval.yaml file.

    Args:
        package: The Python package name (e.g. "my_eval"). The eval.yaml
            file is expected to be in the package directory.

    Returns:
        The version string from eval.yaml (e.g. "1-A").
    """
    yaml_text = resources.files(package).joinpath("eval.yaml").read_text()
    data: dict[str, Any] = yaml.safe_load(yaml_text)
    version = data["version"]
    if not isinstance(version, str):
        raise TypeError(
            f"Expected version to be a string, got {type(version).__name__}"
        )
    return version
