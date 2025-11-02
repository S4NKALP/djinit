"""
Project management for djinit.
Handles creation of Django projects and apps.
"""

import os

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.django_helper import DjangoHelper
from djinit.utils import (
    calculate_app_module_paths,
    extract_existing_apps,
    get_base_settings_path,
    insert_apps_into_user_defined_apps,
    read_base_settings,
)


class ProjectManager:
    def __init__(self, project_dir: str, project_name: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        self.project_root = os.getcwd() if project_dir == "." else os.path.join(os.getcwd(), project_dir)

    def create_project(self) -> bool:
        os.makedirs(self.project_root, exist_ok=True)

        success = DjangoHelper.startproject(self.project_name, self.project_root)
        if success:
            UIFormatter.print_success(f"Django project '{self.project_name}' created successfully!")
        else:
            UIFormatter.print_error(f"Failed to create Django project '{self.project_name}'")
        return success

    def create_apps(self) -> bool:
        apps_base_dir = self.project_root
        nested = bool(self.metadata.get("nested_apps"))
        nested_dir_name = self.metadata.get("nested_dir") if nested else None

        if nested and nested_dir_name:
            apps_base_dir = os.path.join(self.project_root, nested_dir_name)
            os.makedirs(apps_base_dir, exist_ok=True)
            init_file = os.path.join(apps_base_dir, "__init__.py")
            if not os.path.exists(init_file):
                open(init_file, "a").close()

        for app_name in self.app_names:
            success = DjangoHelper.startapp(app_name, apps_base_dir)
            if not success:
                UIFormatter.print_error(f"Failed to create Django app '{app_name}'")
                return False
            UIFormatter.print_success(f"Django app '{app_name}' created successfully!")

        # Add all apps to USER_DEFINED_APPS in settings
        if not self._add_apps_to_settings():
            return False

        return True

    def _add_apps_to_settings(self) -> bool:
        """Add all apps to USER_DEFINED_APPS in base.py settings file."""
        base_settings_path = get_base_settings_path(self.project_root, self.project_name)

        if not os.path.exists(base_settings_path):
            UIFormatter.print_error("Could not find base.py settings file")
            return False

        content = read_base_settings(self.project_root, self.project_name)
        if content is None:
            UIFormatter.print_error("Could not read base.py settings file")
            return False

        app_module_paths = calculate_app_module_paths(self.app_names, self.metadata)

        existing_apps = extract_existing_apps(content)
        apps_to_add = [app for app in app_module_paths if app not in existing_apps]

        if not apps_to_add:
            UIFormatter.print_success("All apps already configured in USER_DEFINED_APPS")
            return True

        updated_content = insert_apps_into_user_defined_apps(content, apps_to_add)
        if not updated_content:
            return False

        with open(base_settings_path, "w") as f:
            f.write(updated_content)

        added_apps_str = ", ".join(apps_to_add)
        UIFormatter.print_success(f"Added apps to USER_DEFINED_APPS: {added_apps_str}")
        return True

    def validate_project_structure(self) -> bool:
        required_files = [
            os.path.join(self.project_root, "manage.py"),
            os.path.join(self.project_root, self.project_name, "__init__.py"),
            os.path.join(self.project_root, self.project_name, "settings", "__init__.py"),
            os.path.join(self.project_root, self.project_name, "settings", "base.py"),
            os.path.join(self.project_root, self.project_name, "settings", "development.py"),
            os.path.join(self.project_root, self.project_name, "settings", "production.py"),
            os.path.join(self.project_root, self.project_name, "urls.py"),
            os.path.join(self.project_root, self.project_name, "wsgi.py"),
            os.path.join(self.project_root, self.project_name, "asgi.py"),
        ]

        apps_base_dir = self.project_root
        if self.metadata.get("nested_apps") and self.metadata.get("nested_dir"):
            apps_base_dir = os.path.join(self.project_root, self.metadata.get("nested_dir"))

        for app_name in self.app_names:
            app_files = [
                os.path.join(apps_base_dir, app_name, "__init__.py"),
                os.path.join(apps_base_dir, app_name, "apps.py"),
                os.path.join(apps_base_dir, app_name, "models.py"),
                os.path.join(apps_base_dir, app_name, "views.py"),
                os.path.join(apps_base_dir, app_name, "serializers.py"),
                os.path.join(apps_base_dir, app_name, "routes.py"),
                os.path.join(apps_base_dir, app_name, "tests.py"),
                os.path.join(apps_base_dir, app_name, "migrations"),
                os.path.join(apps_base_dir, app_name, "admin.py"),
            ]
            required_files.extend(app_files)

        missing_files = []
        for file_path in required_files:
            if file_path.endswith("settings"):
                if not os.path.isdir(file_path):
                    missing_files.append(file_path)
            elif not os.path.exists(file_path):
                missing_files.append(file_path)

        if not missing_files:
            UIFormatter.print_success("Project structure validation passed")
            return True

        UIFormatter.print_error("Project structure validation failed:")
        for file_path in missing_files:
            UIFormatter.print_error(f"  Missing: {file_path}")
        return False
