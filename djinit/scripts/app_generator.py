"""
App management for djinit.
Handles creation of Django apps and updating settings.
"""

import os
import subprocess
from typing import Optional

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.template_engine import template_engine
from djinit.utils import change_cwd, create_file_with_content


class AppManager:
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.current_dir = os.getcwd()
        self.manage_py_path = os.path.join(self.current_dir, "manage.py")

    def create_app(self) -> bool:
        if not self._is_django_project():
            UIFormatter.print_error(
                "Not in a Django project directory. Please run this command from your Django project root."
            )
            return False

        if self._app_exists():
            UIFormatter.print_error(f"Django app '{self.app_name}' already exists.")
            return False

        if not self._create_django_app():
            return False

        if not self._add_to_installed_apps():
            return False

        if not self._create_additional_files():
            return False

        UIFormatter.print_success(f"Django app '{self.app_name}' created and configured successfully!")
        return True

    def _is_django_project(self) -> bool:
        return os.path.exists(self.manage_py_path)

    def _app_exists(self) -> bool:
        # Detect project structure to check in correct location
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()
        app_path = os.path.join(apps_base_dir, self.app_name)
        return os.path.exists(app_path)

    def _create_django_app(self) -> bool:
        # Detect project structure
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()

        # manage.py is always in the project root (current_dir), not in the project directory
        manage_py_path = os.path.join(self.current_dir, "manage.py")
        if not os.path.exists(manage_py_path):
            UIFormatter.print_error("Could not find manage.py file in project root")
            return False

        # Create app in the correct location
        with change_cwd(apps_base_dir):
            subprocess.run(["django-admin", "startapp", self.app_name], capture_output=True, text=True, check=True)

        UIFormatter.print_success(f"Created Django app '{self.app_name}' in {apps_base_dir}")
        return True

    def _add_to_installed_apps(self) -> bool:
        settings_path = self._find_settings_path()
        if not settings_path:
            UIFormatter.print_error("Could not find Django settings directory")
            return False

        base_settings_path = os.path.join(settings_path, "base.py")
        if not os.path.exists(base_settings_path):
            UIFormatter.print_error("Could not find base.py settings file")
            return False

        with open(base_settings_path) as f:
            content = f.read()

        # Detect project structure to determine the correct app module path
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()

        # Determine the correct module path for the app
        if is_nested and nested_dir:
            app_module_path = f"{nested_dir}.{self.app_name}"
        else:
            app_module_path = self.app_name

        # Check if app is already in USER_DEFINED_APPS section specifically
        lines = content.split("\n")
        in_user_apps = False
        app_already_exists = False

        for line in lines:
            if "USER_DEFINED_APPS" in line and "=" in line:
                in_user_apps = True
            elif in_user_apps and line.strip() == "]":
                in_user_apps = False
            elif in_user_apps and (f'"{app_module_path}"' in line or f"'{app_module_path}'" in line):
                app_already_exists = True
                break

        if app_already_exists:
            UIFormatter.print_success(f"App '{app_module_path}' already configured in USER_DEFINED_APPS")
            return True

        if "USER_DEFINED_APPS" not in content:
            UIFormatter.print_error("Could not find USER_DEFINED_APPS section in base.py")
            return False

        lines = content.split("\n")
        new_lines = []
        in_user_apps = False
        apps_added = False

        for line in lines:
            if "USER_DEFINED_APPS" in line and "=" in line:
                in_user_apps = True
                new_lines.append(line)
            elif in_user_apps and line.strip() == "]":
                new_lines.append(f'    "{app_module_path}",')
                new_lines.append(line)
                in_user_apps = False
                apps_added = True
            else:
                new_lines.append(line)

        if not apps_added:
            UIFormatter.print_error("Could not find USER_DEFINED_APPS section in base.py")
            return False

        with open(base_settings_path, "w") as f:
            f.write("\n".join(new_lines))

        UIFormatter.print_success(f"Added '{app_module_path}' to USER_DEFINED_APPS in base.py")
        return True

    def _find_settings_path(self) -> Optional[str]:
        # Look for project directories that contain settings
        for item in os.listdir(self.current_dir):
            if os.path.isdir(item) and not item.startswith(".") and item != "__pycache__":
                # Check if this directory contains Django project files
                project_path = os.path.join(self.current_dir, item)
                settings_path = os.path.join(project_path, "settings")

                # Check if settings directory exists with base.py
                if os.path.exists(settings_path) and os.path.exists(os.path.join(settings_path, "base.py")):
                    return settings_path

        # Fallback: look for settings in current directory
        settings_path = os.path.join(self.current_dir, "settings")
        if os.path.exists(settings_path) and os.path.exists(os.path.join(settings_path, "base.py")):
            return settings_path

        return None

    def _detect_project_structure(self) -> tuple[bool, Optional[str], str]:
        # Step 1: find project directory containing settings/base.py
        project_dir: Optional[str] = None
        settings_base_path: Optional[str] = None
        for item in os.listdir(self.current_dir):
            if os.path.isdir(item) and not item.startswith(".") and item != "__pycache__":
                candidate = os.path.join(self.current_dir, item)
                base_py = os.path.join(candidate, "settings", "base.py")
                if os.path.exists(base_py):
                    project_dir = candidate
                    settings_base_path = base_py
                    break

        # Fallback: current_dir/settings/base.py
        if project_dir is None:
            base_py = os.path.join(self.current_dir, "settings", "base.py")
            if os.path.exists(base_py):
                project_dir = self.current_dir
                settings_base_path = base_py

        if project_dir is None:
            # Not a Django project structure
            return False, None, self.current_dir

        # Step 2: try to infer nested_dir from USER_DEFINED_APPS in base.py
        try:
            if settings_base_path and os.path.exists(settings_base_path):
                with open(settings_base_path) as f:
                    base_content = f.read()
                # Find lines inside USER_DEFINED_APPS and extract first dotted app
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
                                prefix = app_label.split(".", 1)[0]
                                nested_path = os.path.join(self.current_dir, prefix)
                                if os.path.isdir(nested_path):
                                    return True, prefix, nested_path
        except Exception:
            # Ignore parsing issues and continue with heuristics
            pass

        # Step 3: look for existing package directories in project root
        preferred = ["apps", "modules", "packages"]
        for name in preferred:
            nested_path = os.path.join(self.current_dir, name)
            if os.path.isdir(nested_path) and os.path.exists(os.path.join(nested_path, "__init__.py")):
                return True, name, nested_path

        # Any other directory with __init__.py qualifies as a package
        for item in os.listdir(self.current_dir):
            if item in ("__pycache__",) or item.startswith("."):
                continue
            nested_path = os.path.join(self.current_dir, item)
            if os.path.isdir(nested_path) and os.path.exists(os.path.join(nested_path, "__init__.py")):
                return True, item, nested_path

        # Step 4: fallback
        return False, None, self.current_dir

    def _create_additional_files(self) -> bool:
        """Create additional files for the app (serializers.py, routes.py)."""
        # Detect project structure to get correct app path
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()
        app_path = os.path.join(apps_base_dir, self.app_name)

        # Create serializers.py
        context = {"app_name": self.app_name}
        serializers_content = template_engine.render_template("serializers.j2", context)
        create_file_with_content(
            os.path.join(app_path, "serializers.py"),
            serializers_content,
            f"Created {self.app_name}/serializers.py",
            should_format=True,
        )

        # Create routes.py
        routes_content = template_engine.render_template("routes.j2", context)
        create_file_with_content(
            os.path.join(app_path, "routes.py"),
            routes_content,
            f"Created {self.app_name}/routes.py",
            should_format=True,
        )

        return True
