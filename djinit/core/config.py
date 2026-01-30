"""
Core configuration and constants for djinit.
"""

import sys

# Django version used for project generation
DJANGO_VERSION = "6.0.1"

# Reserved names that cannot be used for projects or apps
DJANGO_RESERVED = {"django", "test", "site-packages", "admin"}

# Python builtin module names
PYTHON_BUILTINS = set(sys.builtin_module_names)
