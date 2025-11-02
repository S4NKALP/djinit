"""
App management for djinit.
Handles creation of Django apps and updating settings.
"""

import os
from typing import Optional

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.django_helper import DjangoHelper
from djinit.utils import (
    calculate_app_module_path,
    detect_nested_structure_from_settings,
    extract_existing_apps,
    find_project_dir,
    find_settings_path,
    insert_apps_into_user_defined_apps,
    is_django_project,
)


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
        return is_django_project(self.current_dir)

    def _app_exists(self) -> bool:
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()
        app_path = os.path.join(apps_base_dir, self.app_name)
        return os.path.exists(app_path)

    def _create_django_app(self) -> bool:
        # Find where to create the app (flat or nested structure)
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()

        # Verify manage.py exists in project root
        manage_py_path = os.path.join(self.current_dir, "manage.py")
        if not os.path.exists(manage_py_path):
            UIFormatter.print_error("Could not find manage.py file in project root")
            return False

        success = DjangoHelper.startapp(self.app_name, apps_base_dir)
        if success:
            UIFormatter.print_success(f"Created Django app '{self.app_name}' in {apps_base_dir}")
        else:
            UIFormatter.print_error(f"Failed to create Django app '{self.app_name}'")
        return success

    def _add_to_installed_apps(self) -> bool:
        settings_path = find_settings_path(self.current_dir)
        if not settings_path:
            UIFormatter.print_error("Could not find Django settings directory")
            return False

        base_settings_path = os.path.join(settings_path, "base.py")
        if not os.path.exists(base_settings_path):
            UIFormatter.print_error("Could not find base.py settings file")
            return False

        with open(base_settings_path) as f:
            content = f.read()

        # Get the app's module path (e.g., "apps.users" or just "users")
        is_nested, nested_dir, apps_base_dir = self._detect_project_structure()
        app_module_path = calculate_app_module_path(self.app_name, is_nested, nested_dir)

        # Check if app is already in USER_DEFINED_APPS
        existing_apps = extract_existing_apps(content)
        if app_module_path in existing_apps:
            UIFormatter.print_success(f"App '{app_module_path}' already configured in USER_DEFINED_APPS")
            return True

        if "USER_DEFINED_APPS" not in content:
            UIFormatter.print_error("Could not find USER_DEFINED_APPS section in base.py")
            return False

        # Add app to USER_DEFINED_APPS list in settings file
        updated_content = insert_apps_into_user_defined_apps(content, [app_module_path])
        if not updated_content:
            return False

        with open(base_settings_path, "w") as f:
            f.write(updated_content)

        UIFormatter.print_success(f"Added '{app_module_path}' to USER_DEFINED_APPS in base.py")
        return True

    def _detect_project_structure(self) -> tuple[bool, Optional[str], str]:
        # Find project directory with settings/base.py
        project_dir, settings_base_path = find_project_dir(self.current_dir)

        if project_dir is None:
            return False, None, self.current_dir

        # Detect nested structure from settings file
        return detect_nested_structure_from_settings(settings_base_path, self.current_dir)
