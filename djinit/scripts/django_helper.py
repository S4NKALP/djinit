"""
Django helper module that replicates Django's startproject and startapp functionality.

This module provides functions to create Django projects and apps without requiring Django.
"""

import os

from djinit.scripts.console_ui import UIFormatter
from djinit.utils import (
    create_directory_with_init,
    create_file_from_template,
    create_files_from_templates,
    create_init_file,
)


class DjangoHelper:
    # Django version to use in generated files (matches Django 5.2)
    DJANGO_VERSION = "5.2"

    @staticmethod
    def startproject(project_name: str, directory: str, unified: bool = False) -> bool:
        try:
            os.makedirs(directory, exist_ok=True)

            # Create manage.py
            manage_py_path = os.path.join(directory, "manage.py")
            create_file_from_template(manage_py_path, "shared/manage_py.j2", {}, "Created manage.py")
            os.chmod(manage_py_path, 0o755)

            # For unified structure, the project config is "core", not project_name
            # The unified structure is created separately by create_unified_structure
            if unified:
                # Just create manage.py for unified, structure is created by create_unified_structure
                return True

            # Create project config directory
            project_config_dir = os.path.join(directory, project_name)
            create_directory_with_init(project_config_dir, f"Created {project_name}/__init__.py")

            # Create settings directory and files
            settings_dir = os.path.join(project_config_dir, "settings")
            create_directory_with_init(settings_dir, f"Created {project_name}/settings/__init__.py")

            base_context = {"project_name": project_name, "app_names": []}
            settings_files = [
                ("base.py", "project/settings/base.j2", base_context),
                ("development.py", "project/settings/development.j2", {}),
                ("production.py", "project/settings/production.j2", {}),
            ]
            create_files_from_templates(settings_dir, settings_files, f"{project_name}/settings/")

            # Create project-level files
            urls_context = {"project_name": project_name, "django_version": DjangoHelper.DJANGO_VERSION}
            project_files = [
                ("urls.py", "project/urls.j2", urls_context),
                ("wsgi.py", "project/wsgi.j2", {}),
                ("asgi.py", "project/asgi.j2", {}),
            ]
            create_files_from_templates(project_config_dir, project_files, f"{project_name}/")

            return True

        except Exception as e:
            UIFormatter.print_error(f"Error creating Django project: {e}")
            return False

    @staticmethod
    def startapp(app_name: str, directory: str) -> bool:
        try:
            app_dir = os.path.join(directory, app_name)
            os.makedirs(app_dir, exist_ok=True)

            context = {"app_name": app_name, "django_version": DjangoHelper.DJANGO_VERSION}

            # Create app files
            create_init_file(app_dir, f"Created {app_name}/__init__.py")

            app_files = [
                ("apps.py", "base/apps.j2", context),
                ("models.py", "base/models.j2", context),
                ("views.py", "base/views.j2", context),
                ("admin.py", "base/admin.j2", context),
                ("urls.py", "base/urls.j2", context),
                ("serializers.py", "base/serializers.j2", context),
                ("routes.py", "base/routes.j2", context),
                ("tests.py", "base/tests.j2", context),
            ]

            create_files_from_templates(app_dir, app_files, f"{app_name}/")

            # Create migrations directory and __init__.py
            migrations_dir = os.path.join(app_dir, "migrations")
            create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

            return True

        except Exception as e:
            UIFormatter.print_error(f"Error creating Django app: {e}")
            return False
