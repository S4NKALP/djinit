"""
Project management for djinit.
Handles creation of Django projects and apps.
"""

import os

from djinit.ui.console import UIFormatter
from djinit.utils.common import (
    calculate_app_module_paths,
    create_directory_with_init,
    extract_existing_apps,
    get_base_settings_path,
    insert_apps_into_user_defined_apps,
    read_base_settings,
)
from djinit.utils.django import DjangoHelper


class ProjectManager:
    def __init__(self, project_dir: str, project_name: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        self.project_root = os.getcwd() if project_dir == "." else os.path.join(os.getcwd(), project_dir)
        self.module_name = metadata.get("project_module_name") or self.project_name

    def create_project(self) -> None:
        os.makedirs(self.project_root, exist_ok=True)

        unified = self.metadata.get("unified_structure", False)
        DjangoHelper.startproject(self.module_name, self.project_root, unified=unified)
        UIFormatter.print_success(f"Django project '{self.project_name}' created successfully!")

    def _get_apps_base_dir(self) -> str:
        """Get the base directory for apps, considering nested structure."""
        apps_base_dir = self.project_root
        if self.metadata.get("nested_apps") and self.metadata.get("nested_dir"):
            apps_base_dir = os.path.join(self.project_root, self.metadata.get("nested_dir"))
        return apps_base_dir

    def create_apps(self) -> None:
        apps_base_dir = self._get_apps_base_dir()

        if apps_base_dir != self.project_root:
            create_directory_with_init(apps_base_dir, f"Created {os.path.basename(apps_base_dir)}/__init__.py")

        for app_name in self.app_names:
            DjangoHelper.startapp(app_name, apps_base_dir)
            UIFormatter.print_success(f"Django app '{app_name}' created successfully!")

        self.add_apps_to_settings()

    def add_apps_to_settings(self) -> None:
        """Add all apps to USER_DEFINED_APPS in base.py settings file."""
        base_settings_path = get_base_settings_path(self.project_root, self.module_name)

        if not os.path.exists(base_settings_path):
            from djinit.utils.exceptions import ConfigError

            raise ConfigError("Could not find base.py settings file")

        content = read_base_settings(self.project_root, self.module_name)
        if content is None:
            from djinit.utils.exceptions import ConfigError

            raise ConfigError("Could not read base.py settings file")

        app_module_paths = calculate_app_module_paths(self.app_names, self.metadata)

        existing_apps = extract_existing_apps(content)
        apps_to_add = [app for app in app_module_paths if app not in existing_apps]

        if not apps_to_add:
            UIFormatter.print_success("All apps already configured in USER_DEFINED_APPS")
            return

        updated_content = insert_apps_into_user_defined_apps(content, apps_to_add)
        if not updated_content:
            from djinit.utils.exceptions import ConfigError

            raise ConfigError("Could not update USER_DEFINED_APPS in base.py")

        with open(base_settings_path, "w") as f:
            f.write(updated_content)

        added_apps_str = ", ".join(apps_to_add)
        UIFormatter.print_success(f"Added apps to USER_DEFINED_APPS: {added_apps_str}")

    def validate_project_structure(self) -> None:
        join = lambda *args: os.path.join(self.project_root, *args)

        required_files = [
            join("manage.py"),
            join(self.module_name, "__init__.py"),
            join(self.module_name, "settings", "__init__.py"),
            join(self.module_name, "settings", "base.py"),
            join(self.module_name, "settings", "development.py"),
            join(self.module_name, "settings", "production.py"),
            join(self.module_name, "urls.py"),
            join(self.module_name, "wsgi.py"),
            join(self.module_name, "asgi.py"),
        ]

        apps_base_dir = self._get_apps_base_dir()

        if self.metadata.get("unified_structure"):
            # Validate Unified Structure
            apps_dir = join("apps")
            unified_files = [
                os.path.join(apps_dir, "__init__.py"),
                os.path.join(apps_dir, "apps.py"),
                os.path.join(apps_dir, "admin", "__init__.py"),
                os.path.join(apps_dir, "api", "__init__.py"),
                os.path.join(apps_dir, "api", "urls.py"),
                os.path.join(apps_dir, "api", "v1", "__init__.py"),
                os.path.join(apps_dir, "api", "v1", "urls.py"),
                os.path.join(apps_dir, "models", "__init__.py"),
                os.path.join(apps_dir, "serializers", "__init__.py"),
                os.path.join(apps_dir, "tests", "__init__.py"),
                os.path.join(apps_dir, "urls", "__init__.py"),
                os.path.join(apps_dir, "views", "__init__.py"),
            ]
            required_files.extend(unified_files)

        elif not self.metadata.get("predefined_structure") and not self.metadata.get("single_structure"):
            for app_name in self.app_names:
                app_path = lambda f, app=app_name: os.path.join(apps_base_dir, app, f)
                app_files = [
                    app_path("__init__.py"),
                    app_path("apps.py"),
                    app_path("models.py"),
                    app_path("views.py"),
                    app_path("serializers.py"),
                    app_path("routes.py"),
                    app_path("tests.py"),
                    app_path("migrations"),
                    app_path("admin.py"),
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
            return

        UIFormatter.print_error("Project structure validation failed:")
        for file_path in missing_files:
            UIFormatter.print_error(f"  Missing: {file_path}")

        from djinit.utils.exceptions import ConfigError

        raise ConfigError("Project structure validation failed", details=f"Missing files: {missing_files}")
