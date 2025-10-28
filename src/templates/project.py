"""
Project management for djinit.
Handles creation of Django projects and apps.
"""

import os
import subprocess
import sys

from src.scripts.console_ui import UIFormatter
from src.utils import change_cwd


class ProjectManager:
    def __init__(self, project_dir: str, project_name: str, app_names: list):
        self.project_dir = project_dir
        self.project_name = project_name
        self.app_names = app_names
        self.project_root = os.path.join(os.getcwd(), project_dir)

    def create_project(self) -> bool:
        # Check if project already exists
        if os.path.exists(self.project_root):
            UIFormatter.print_error(f"Directory '{self.project_dir}' already exists.")
            UIFormatter.print_info("Please choose a different project directory name or remove the existing directory.")
            return False

        # Ensure Django is installed
        self._ensure_django_installed()

        # Create the project directory first
        os.makedirs(self.project_root, exist_ok=True)

        # Create Django project inside the directory
        subprocess.run(
            ["django-admin", "startproject", self.project_name, self.project_root],
            check=True,
        )

        UIFormatter.print_success(f"Django project '{self.project_name}' created successfully!")
        return True

    def create_apps(self) -> bool:
        with change_cwd(self.project_root):
            # Create each app
            for app_name in self.app_names:
                try:
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
                except subprocess.CalledProcessError as e:
                    UIFormatter.print_error(f"Failed to create app '{app_name}': {e}")
                    return False

        return True

    def _ensure_django_installed(self) -> None:
        try:
            import django
        except ImportError:
            UIFormatter.print_info("Django not found, installing...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "django"],
                check=True,
            )
            UIFormatter.print_success("Django installed successfully!")

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
        for app_name in self.app_names:
            app_files = [
                os.path.join(self.project_root, app_name, "__init__.py"),
                os.path.join(self.project_root, app_name, "apps.py"),
                os.path.join(self.project_root, app_name, "models.py"),
                os.path.join(self.project_root, app_name, "views.py"),
                os.path.join(self.project_root, app_name, "admin.py"),
            ]
            required_files.extend(app_files)

        missing_files = [file_path for file_path in required_files if not os.path.exists(file_path)]

        if missing_files:
            UIFormatter.print_error("Project structure validation failed:")
            for file_path in missing_files:
                UIFormatter.print_error(f"  Missing: {file_path}")
            return False

        UIFormatter.print_success("Project structure validation passed")
        return True
