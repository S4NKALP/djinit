"""
Shared utility functions.
Contains common operations used across multiple managers.
"""

import os
import subprocess
import sys
from contextlib import contextmanager

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.template_engine import template_engine


def format_file(filename: str) -> None:
    """Format Python file using Ruff formatter."""
    subprocess.run([sys.executable, "-m", "ruff", "format", filename], check=False, capture_output=True)


# create a file with content, optionally format it
def create_file_with_content(filename: str, content: str, success_message: str, should_format: bool = False) -> bool:
    with open(filename, "w") as file:
        file.write(content)

    if should_format:
        format_file(filename)

    # UIFormatter.print_success(success_message)
    return True


# create a file from a template
def create_file_from_template(
    file_path: str,
    template_path: str,
    context: dict,
    success_message: str,
    should_format: bool = True,
) -> None:
    content = template_engine.render_template(template_path, context)
    create_file_with_content(file_path, content, success_message, should_format=should_format)


# create __init__.py
def create_init_file(directory: str, success_message: str) -> None:
    init_path = os.path.join(directory, "__init__.py")
    create_file_from_template(init_path, "shared/init.j2", {}, success_message, should_format=False)


# change the current working dir tempporary
@contextmanager
def change_cwd(path: str):
    original_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


# get app names from USER_DEFINED_APPS section in project_name/settings/base.py
def extract_existing_apps(content: str) -> set:
    lines = content.split("\n")
    existing_apps = set()
    in_user_apps = False

    for line in lines:
        if "USER_DEFINED_APPS" in line and "=" in line:
            in_user_apps = True
        elif in_user_apps and line.strip() == "]":
            break
        elif in_user_apps:
            line_stripped = line.strip().strip(",").strip()
            for quote in ('"', "'"):
                if line_stripped.startswith(quote) and line_stripped.endswith(quote):
                    existing_apps.add(line_stripped.strip(quote))
                    break

    return existing_apps


# format app names as list entries with proper indentation
def format_app_entries(apps: list) -> list:
    return [f'    "{app}",' for app in apps]


# check if line starts a new APP section
def is_app_section_start(line: str) -> bool:
    return "=" in line and any(keyword in line for keyword in ("BUILT_IN_APPS", "THIRD_PARTY_APPS", "INSTALLED_APPS"))


# check if closing bracket belongs to USER_DEFINED_APPS by looking ahead
def is_user_apps_closing_bracket(lines: list, current_idx: int) -> bool:
    for next_idx in range(current_idx + 1, min(current_idx + 3, len(lines))):
        next_line = lines[next_idx].strip()
        if next_line and "BUILT_IN_APPS" in next_line:
            return True
    return True  # Default to True if we're inside USER_DEFINED_APPS


# split line with closing bracnket and insert apps
def split_bracket_line(line: str, apps_to_add: list) -> list:
    bracket_pos = line.rfind("]")
    before_bracket = line[:bracket_pos].rstrip() if bracket_pos > 0 else line.rstrip()
    after_bracket = line[bracket_pos:] if bracket_pos > 0 else "]"

    result = [before_bracket]
    result.extend(format_app_entries(apps_to_add))
    result.append(after_bracket)
    return result


# insert apps into USER_DEFINED_APPS section before the closing bracket.
def insert_apps_into_user_defined_apps(content: str, apps_to_add: list) -> str:
    lines = content.split("\n")
    new_lines = []
    in_user_apps = False
    apps_added = False

    for i, line in enumerate(lines):
        # Entering USER_DEFINED_APPS section
        if "USER_DEFINED_APPS" in line and "=" in line and not apps_added:
            in_user_apps = True

            # Handle closing bracket on same line
            if "]" in line:
                new_lines.extend(split_bracket_line(line, apps_to_add))
                apps_added = True
                in_user_apps = False
            else:
                new_lines.append(line)

        # Closing bracket on separate line
        elif in_user_apps and line.strip() == "]" and not apps_added:
            if is_user_apps_closing_bracket(lines, i):
                new_lines.extend(format_app_entries(apps_to_add))
                new_lines.append(line)
                apps_added = True
                in_user_apps = False
            else:
                new_lines.append(line)

        # Safety: hit another APP section without closing bracket
        elif in_user_apps and is_app_section_start(line) and not apps_added:
            new_lines.extend(format_app_entries(apps_to_add))
            new_lines.append("]")
            new_lines.append(line)
            apps_added = True
            in_user_apps = False

        else:
            new_lines.append(line)

    if not apps_added:
        UIFormatter.print_error("Could not find or update USER_DEFINED_APPS section in base.py")
        return None

    return "\n".join(new_lines)


# calculate app module paths based on nested structure
def calculate_app_module_paths(app_names: list, metadata: dict) -> list:
    nested = bool(metadata.get("nested_apps"))
    nested_dir_name = metadata.get("nested_dir") if nested else None
    return [f"{nested_dir_name}.{app_name}" if nested and nested_dir_name else app_name for app_name in app_names]


# calculate app module path for a single app
def calculate_app_module_path(app_name: str, nested: bool, nested_dir: str | None) -> str:
    return f"{nested_dir}.{app_name}" if nested and nested_dir else app_name


# check if a dir is a Django project by looking for manage.py
def is_django_project(directory: str = None) -> bool:
    if directory is None:
        directory = os.getcwd()
    manage_py_path = os.path.join(directory, "manage.py")
    return os.path.exists(manage_py_path)


# search the project dir that contains settings/base.py
def find_project_dir(search_dir: str = None) -> tuple[str | None, str | None]:
    if search_dir is None:
        search_dir = os.getcwd()

    for item in os.listdir(search_dir):
        if os.path.isdir(item) and not item.startswith(".") and item != "__pycache__":
            candidate = os.path.join(search_dir, item)
            base_py = os.path.join(candidate, "settings", "base.py")
            if os.path.exists(base_py):
                return candidate, base_py
    return None, None


# search the project_name/settings dir path
def find_settings_path(search_dir: str = None) -> str | None:
    project_dir, settings_base_path = find_project_dir(search_dir)
    if settings_base_path:
        return os.path.dirname(settings_base_path)
    return None


# get the path to project_name/settings/base.py
def get_base_settings_path(project_root: str, project_name: str) -> str:
    settings_dir = os.path.join(project_root, project_name, "settings")
    return os.path.join(settings_dir, "base.py")


# read the content of project_name/settings/base.py
def read_base_settings(project_root: str, project_name: str) -> str | None:
    base_settings_path = get_base_settings_path(project_root, project_name)
    if not os.path.exists(base_settings_path):
        return None

    with open(base_settings_path) as f:
        return f.read()


# check for nested app structure(e.g: "apps.users" means nested) from project_name/settings/base.py
def detect_nested_structure_from_settings(
    base_settings_path: str, search_dir: str = None
) -> tuple[bool, str | None, str]:
    if search_dir is None:
        search_dir = os.getcwd()

    if not os.path.exists(base_settings_path):
        return False, None, search_dir

    try:
        with open(base_settings_path) as f:
            base_content = f.read()

        in_user_apps = False
        for line in base_content.splitlines():
            if "USER_DEFINED_APPS" in line and "=" in line:
                in_user_apps = True
                continue
            if in_user_apps and "]" in line:
                break
            if in_user_apps:
                line_stripped = line.strip().strip(",")
                if line_stripped.startswith('"') or line_stripped.startswith("'"):
                    app_label = line_stripped.strip("\"'")
                    if "." in app_label:
                        nested_dir_name = app_label.split(".", 1)[0]
                        nested_path = os.path.join(search_dir, nested_dir_name)
                        if os.path.isdir(nested_path):
                            return True, nested_dir_name, nested_path
    except Exception:
        pass

    return False, None, search_dir
