"""
App management for Django project setup.
Handles creation of Django apps and updating settings.
"""

import os
import subprocess
from typing import Optional

from src.scripts.console_ui import UIFormatter


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

        UIFormatter.print_success(f"Django app '{self.app_name}' created and configured successfully!")
        return True

    def _is_django_project(self) -> bool:
        return os.path.exists(self.manage_py_path)

    def _app_exists(self) -> bool:
        app_path = os.path.join(self.current_dir, self.app_name)
        return os.path.exists(app_path)

    def _create_django_app(self) -> bool:
        result = subprocess.run(["django-admin", "startapp", self.app_name], capture_output=True, text=True, check=True)

        UIFormatter.print_success(f"Created Django app '{self.app_name}'")
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

        if f'"{self.app_name}"' in content or f"'{self.app_name}'" in content:
            UIFormatter.print_info(f"App '{self.app_name}' is already in INSTALLED_APPS")
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
                new_lines.append(f'    "{self.app_name}",')
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

        UIFormatter.print_success(f"Added '{self.app_name}' to USER_DEFINED_APPS in base.py")
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
