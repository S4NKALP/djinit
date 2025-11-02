"""
Project management for djinit.
Handles creation of Django projects and apps.
"""

import importlib.util
import os
import subprocess
import sys

from djinit.scripts.console_ui import UIFormatter
from djinit.utils import change_cwd


class ProjectManager:
    def __init__(self, project_dir: str, project_name: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        # Handle '.' for current directory
        if project_dir == ".":
            self.project_root = os.getcwd()
        else:
            self.project_root = os.path.join(os.getcwd(), project_dir)

    def create_project(self) -> bool:
        self._ensure_django_installed()

        # Create the project directory first
        os.makedirs(self.project_root, exist_ok=True)

        # Create Django project inside the directory
        # Use 'python -m django' instead of 'django-admin' for better compatibility
        subprocess.run(
            [sys.executable, "-m", "django", "startproject", self.project_name, self.project_root],
            check=True,
        )

        UIFormatter.print_success(f"Django project '{self.project_name}' created successfully!")
        return True

    def create_apps(self) -> bool:
        # Determine base directory for apps
        apps_base_dir = self.project_root
        nested = bool(self.metadata.get("nested_apps"))
        nested_dir_name = self.metadata.get("nested_dir") if nested else None

        if nested and nested_dir_name:
            apps_base_dir = os.path.join(self.project_root, nested_dir_name)
            os.makedirs(apps_base_dir, exist_ok=True)
            # Make it a Python package
            init_file = os.path.join(apps_base_dir, "__init__.py")
            if not os.path.exists(init_file):
                open(init_file, "a").close()

        with change_cwd(apps_base_dir):
            # Create each app
            for app_name in self.app_names:
                subprocess.run(
                    [
                        sys.executable,
                        os.path.join(self.project_root, "manage.py"),
                        "startapp",
                        app_name,
                    ],
                    check=True,
                )
                UIFormatter.print_success(f"Django app '{app_name}' created successfully!")

        return True

    def _ensure_django_installed(self) -> None:
        if importlib.util.find_spec("django") is None:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "django", "-q"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def validate_project_structure(self) -> bool:
        required_files = [
            os.path.join(self.project_root, "manage.py"),
            os.path.join(self.project_root, self.project_name, "__init__.py"),
            os.path.join(self.project_root, self.project_name, "settings.py"),
            os.path.join(self.project_root, self.project_name, "urls.py"),
            os.path.join(self.project_root, self.project_name, "wsgi.py"),
            os.path.join(self.project_root, self.project_name, "asgi.py"),
        ]

        # Add required files for each app
        apps_base_dir = self.project_root
        if self.metadata.get("nested_apps") and self.metadata.get("nested_dir"):
            apps_base_dir = os.path.join(self.project_root, self.metadata.get("nested_dir"))

        for app_name in self.app_names:
            app_files = [
                os.path.join(apps_base_dir, app_name, "__init__.py"),
                os.path.join(apps_base_dir, app_name, "apps.py"),
                os.path.join(apps_base_dir, app_name, "models.py"),
                os.path.join(apps_base_dir, app_name, "views.py"),
                os.path.join(apps_base_dir, app_name, "admin.py"),
            ]
            required_files.extend(app_files)

        missing_files = [file_path for file_path in required_files if not os.path.exists(file_path)]

        if not missing_files:
            UIFormatter.print_success("Project structure validation passed")
            return True

        UIFormatter.print_error("Project structure validation failed:")
        for file_path in missing_files:
            UIFormatter.print_error(f"  Missing: {file_path}")
        return False
