"""
Input validation utilities for Django project setup.
Handles validation of project names, app names, and other user inputs.
"""

import keyword
import re
from typing import Any, Callable, Tuple

from djinit.core.config import PYTHON_BUILTINS

NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def _validate_name(name: str, name_type: str = "name") -> Tuple[bool, str]:
    validation_rules: list[Tuple[Callable[[str], Any], str]] = [
        (lambda n: bool(n and n.strip()), f"{name_type.capitalize()} cannot be empty"),
        (lambda n: len(n.strip()) >= 2, f"{name_type.capitalize()} must be at least 2 characters long"),
        (lambda n: len(n.strip()) <= 50, f"{name_type.capitalize()} must be less than 50 characters"),
        (
            lambda n: NAME_PATTERN.match(n.strip()),
            f"{name_type.capitalize()} must start with a letter and contain only letters, numbers, and underscores",
        ),
        (
            lambda n: not keyword.iskeyword(n.strip()),
            f"'{name.strip()}' is a Python keyword. Please choose a different name",
        ),
        (
            lambda n: n.strip().lower() not in PYTHON_BUILTINS,
            f"'{name.strip()}' conflicts with Python builtin module. Choose a different name",
        ),
        (lambda n: not n.strip().startswith("_"), f"{name_type.capitalize()} should not start with underscore"),
    ]

    for rule, error_message in validation_rules:
        if not rule(name):
            return False, error_message

    return True, ""


def validate_project_name(name: str) -> Tuple[bool, str]:
    return _validate_name(name, "project name")


def validate_app_name(name: str) -> Tuple[bool, str]:
    return _validate_name(name, "app name")
