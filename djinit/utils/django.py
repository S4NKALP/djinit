"""
Django helper module that replicates Django's startproject and startapp functionality.

This module provides functions to create Django projects and apps without requiring Django.
"""

import os

from djinit.core.config import DJANGO_VERSION
from djinit.utils.common import (
    create_directory_with_init,
    create_file_from_template,
    create_files_from_templates,
    create_init_file,
)


class DjangoHelper:
    DJANGO_VERSION = DJANGO_VERSION

    @staticmethod
    def startproject(project_name: str, directory: str, unified: bool = False) -> None:
        try:
            os.makedirs(directory, exist_ok=True)

            manage_py_path = os.path.join(directory, "manage.py")
            create_file_from_template(manage_py_path, "project/manage_py.j2", {}, "Created manage.py")
            os.chmod(manage_py_path, 0o755)

            if unified:
                return

            project_config_dir = os.path.join(directory, project_name)
            create_directory_with_init(project_config_dir, f"Created {project_name}/__init__.py")

            settings_dir = os.path.join(project_config_dir, "settings")
            create_directory_with_init(settings_dir, f"Created {project_name}/settings/__init__.py")

            base_context = {"project_name": project_name, "app_names": []}
            settings_files = [
                ("base.py", "config/settings/base.j2", base_context),
                ("development.py", "config/settings/development.j2", {}),
                ("production.py", "config/settings/production.j2", {}),
            ]
            create_files_from_templates(settings_dir, settings_files, f"{project_name}/settings/")

            urls_context = {"project_name": project_name, "django_version": DjangoHelper.DJANGO_VERSION}
            project_files = [
                ("urls.py", "config/urls/base.j2", urls_context),
                ("wsgi.py", "config/wsgi.j2", {}),
                ("asgi.py", "config/asgi.j2", {}),
            ]
            create_files_from_templates(project_config_dir, project_files, f"{project_name}/")

        except Exception as e:
            from djinit.utils.exceptions import DjinitError

            raise DjinitError(f"Error creating Django project: {e}", details=str(e)) from e

    @staticmethod
    def startapp(app_name: str, directory: str) -> None:
        try:
            app_dir = os.path.join(directory, app_name)
            os.makedirs(app_dir, exist_ok=True)

            context = {"app_name": app_name, "django_version": DjangoHelper.DJANGO_VERSION}

            create_init_file(app_dir, f"Created {app_name}/__init__.py")

            app_files = [
                ("apps.py", "components/apps.j2", context),
                ("models.py", "components/models.j2", context),
                ("views.py", "components/views.j2", context),
                ("admin.py", "components/admin.j2", context),
                ("urls.py", "components/urls.j2", context),
                ("serializers.py", "components/serializers.j2", context),
                ("routes.py", "components/routes.j2", context),
                ("tests.py", "components/tests.j2", context),
            ]

            create_files_from_templates(app_dir, app_files, f"{app_name}/")

            migrations_dir = os.path.join(app_dir, "migrations")
            create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        except Exception as e:
            from djinit.utils.exceptions import DjinitError

            raise DjinitError(f"Error creating Django app: {e}", details=str(e)) from e
