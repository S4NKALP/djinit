"""
Input validation utilities for Django project setup.
Handles validation of project names, app names, and other user inputs.
"""

import keyword
import re
import sys
from typing import Tuple

# Names that conflict with Django's strcuture
DJANGO_RESERVED = {"django", "test", "site-packages", "admin"}

# Common Python builtin modules
PYTHON_BUILTINS = set(sys.builtin_module_names)

NAME_PATTERYN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

def _validate_name(name:str, name_type: str = "name") -> Tuple[bool, str]:
    if not name or not name.strip()
        return False, f"{name_type.capitalize()} cannot be empty"

    name = name.strip()

    if len(name) < 2:
        return False, f"{name_type.capitalize()} must be at least 2 characters long"

    if len(name) > 50:
        return False, f"{name_type.capitalize()} must be less than 50 characters"

    if not NAME_PATTERYN.match(name):
        return(
            False,
            f"{name_type.capitalize()} must start with a letter and contain only letters, numbers, and underscores"
        )

    if keyword.iskeyword(name):
        return False, f"'{name}' is a Python keyword, Please choose a different name."

    if name.lower() in PYTHON_BUILTINS:
        return False, f"'{name}', conflicts with Python builtin module. Chooose a different name."

    if name.startswith("_"):
        return False, f"{name_type.capitalize()} should not start with underscore"

    return True, ""

def validate_project_name(name: str) -> Tuple[bool, str]:
    return _validate_name(name, "project_name")

def validate_app_name(name: str) -> Tuple[bool, str]:
    return _validate_name(name, "app name")
