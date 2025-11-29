"""
Shared utility functions.
Contains common operations used across multiple managers.
"""

import os
import subprocess
import sys
from contextlib import contextmanager

from djinit.services.templates import template_engine
from djinit.ui.console import UIFormatter


def format_file(filename: str) -> None:
    """Format Python file using Ruff formatter."""
    subprocess.run([sys.executable, "-m", "ruff", "format", filename], check=False, capture_output=True)


def create_file_with_content(filename: str, content: str, success_message: str, should_format: bool = False) -> None:
    from djinit.utils.exceptions import FileError

    try:
        with open(filename, "w") as file:
            file.write(content)
    except OSError as e:
        raise FileError(f"Failed to write file: {filename}", details=str(e)) from e

    if should_format:
        format_file(filename)

    UIFormatter.print_success(success_message)


def create_file_from_template(
    file_path: str,
    template_path: str,
    context: dict,
    success_message: str,
    should_format: bool = True,
) -> None:
    try:
        content = template_engine.render_template(template_path, context)
    except Exception as e:
        from djinit.utils.exceptions import TemplateError

        raise TemplateError(f"Failed to render template: {template_path}", details=str(e)) from e

    create_file_with_content(file_path, content, success_message, should_format=should_format)


def create_init_file(directory: str, success_message: str) -> None:
    init_path = os.path.join(directory, "__init__.py")
    create_file_from_template(init_path, "project/init.j2", {}, success_message, should_format=False)


def create_directory_with_init(dir_path: str, message: str) -> None:
    """Create directory and __init__.py file."""
    os.makedirs(dir_path, exist_ok=True)
    create_init_file(dir_path, message)


def create_files_from_templates(base_dir: str, files: list, prefix: str = "", should_format: bool = False) -> None:
    """Create multiple files from templates.

    Args:
        base_dir: Base directory where files will be created
        files: List of tuples (filename, template_path, context)
        prefix: Optional prefix for success message
        should_format: Whether to format the created files
    """
    for file_spec in files:
        if len(file_spec) == 3:
            filename, template_path, context = file_spec
        else:
            # Support (filename, template_path) format with empty context
            filename, template_path = file_spec
            context = {}
        filepath = os.path.join(base_dir, filename)
        message = f"Created {prefix}{filename}" if prefix else f"Created {filename}"
        create_file_from_template(filepath, template_path, context, message, should_format=should_format)


def get_package_name(project_dir: str) -> str:
    """Get package name, defaulting to 'backend' if project_dir is '.' or empty."""
    return "backend" if project_dir == "." or not project_dir else project_dir


@contextmanager
def change_cwd(path: str):
    original_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


def _parse_app_entry_from_line(line: str) -> str | None:
    """Extract app name from a line in USER_DEFINED_APPS section."""
    line_stripped = line.strip().strip(",").strip()
    for quote in ('"', "'"):
        if line_stripped.startswith(quote) and line_stripped.endswith(quote):
            return line_stripped.strip(quote)
    return None


def _is_user_apps_section_start(line: str) -> bool:
    """Check if line starts USER_DEFINED_APPS section."""
    return "USER_DEFINED_APPS" in line and "=" in line


def _iterate_user_apps_lines(content: str):
    """Generator that yields lines within USER_DEFINED_APPS section."""
    lines = content.split("\n")
    in_user_apps = False

    for line in lines:
        if _is_user_apps_section_start(line):
            in_user_apps = True
        elif in_user_apps and line.strip() == "]":
            break
        elif in_user_apps:
            yield line


def extract_existing_apps(content: str) -> set:
    existing_apps = set()
    for line in _iterate_user_apps_lines(content):
        app_name = _parse_app_entry_from_line(line)
        if app_name:
            existing_apps.add(app_name)
    return existing_apps


def format_app_entries(apps: list) -> list:
    return [f'    "{app}",' for app in apps]


def is_app_section_start(line: str) -> bool:
    return "=" in line and any(keyword in line for keyword in ("BUILT_IN_APPS", "THIRD_PARTY_APPS", "INSTALLED_APPS"))


def is_user_apps_closing_bracket(lines: list, current_idx: int) -> bool:
    for next_idx in range(current_idx + 1, min(current_idx + 3, len(lines))):
        next_line = lines[next_idx].strip()
        if next_line and "BUILT_IN_APPS" in next_line:
            return True
    return True  # Default to True if we're inside USER_DEFINED_APPS


def split_bracket_line(line: str, apps_to_add: list) -> list:
    bracket_pos = line.rfind("]")
    before_bracket = line[:bracket_pos].rstrip() if bracket_pos > 0 else line.rstrip()
    after_bracket = line[bracket_pos:] if bracket_pos > 0 else "]"

    result = [before_bracket]
    result.extend(format_app_entries(apps_to_add))
    result.append(after_bracket)
    return result


def insert_apps_into_user_defined_apps(content: str, apps_to_add: list) -> str:
    lines = content.split("\n")
    new_lines = []
    in_user_apps = False
    apps_added = False

    for i, line in enumerate(lines):
        if _is_user_apps_section_start(line) and not apps_added:
            in_user_apps = True

            if "]" in line:
                new_lines.extend(split_bracket_line(line, apps_to_add))
                apps_added = True
                in_user_apps = False
            else:
                new_lines.append(line)

        elif in_user_apps and line.strip() == "]" and not apps_added:
            if is_user_apps_closing_bracket(lines, i):
                new_lines.extend(format_app_entries(apps_to_add))
                new_lines.append(line)
                apps_added = True
                in_user_apps = False
            else:
                new_lines.append(line)

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


def calculate_app_module_paths(app_names: list, metadata: dict) -> list:
    nested = bool(metadata.get("nested_apps"))
    nested_dir_name = metadata.get("nested_dir") if nested else None
    return [calculate_app_module_path(app_name, nested, nested_dir_name) for app_name in app_names]


def calculate_app_module_path(app_name: str, nested: bool, nested_dir: str | None) -> str:
    return f"{nested_dir}.{app_name}" if nested and nested_dir else app_name


def is_django_project(directory: str = None) -> bool:
    if directory is None:
        directory = os.getcwd()
    manage_py_path = os.path.join(directory, "manage.py")
    return os.path.exists(manage_py_path)


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


def find_settings_path(search_dir: str = None) -> str | None:
    project_dir, settings_base_path = find_project_dir(search_dir)
    if settings_base_path:
        return os.path.dirname(settings_base_path)
    return None


def get_base_settings_path(project_root: str, project_name: str) -> str:
    settings_dir = os.path.join(project_root, project_name, "settings")
    return os.path.join(settings_dir, "base.py")


def read_base_settings(project_root: str, project_name: str) -> str | None:
    base_settings_path = get_base_settings_path(project_root, project_name)
    if not os.path.exists(base_settings_path):
        return None

    with open(base_settings_path) as f:
        return f.read()


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

        for line in _iterate_user_apps_lines(base_content):
            app_label = _parse_app_entry_from_line(line)
            if app_label and "." in app_label:
                nested_dir_name = app_label.split(".", 1)[0]
                nested_path = os.path.join(search_dir, nested_dir_name)
                if os.path.isdir(nested_path):
                    return True, nested_dir_name, nested_path
    except Exception:
        pass

    return False, None, search_dir


def get_djinit_config(project_root: str = None) -> dict | None:
    """Read .djinit configuration file."""
    import json

    if project_root is None:
        project_root = os.getcwd()

    config_path = os.path.join(project_root, ".djinit")
    if not os.path.exists(config_path):
        # Try finding it in parent directories
        parent = os.path.dirname(project_root)
        if parent and parent != project_root:
            return get_djinit_config(parent)
        return None

    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception:
        return None
