"""
Django helper module that replicates Django's startproject and startapp functionality.

This module provides functions to create Django projects and apps without requiring Django.
"""

import os

from djinit.scripts.console_ui import UIFormatter
from djinit.utils import create_file_from_template, create_init_file


class DjangoHelper:
    # Django version to use in generated files (matches Django 5.2)
    DJANGO_VERSION = "5.2"

    @staticmethod
    def startproject(project_name: str, directory: str) -> bool:
        try:
            os.makedirs(directory, exist_ok=True)

            # Create manage.py
            manage_py_path = os.path.join(directory, "manage.py")
            create_file_from_template(manage_py_path, "project/manage_py.j2", {}, "Created manage.py")
            os.chmod(manage_py_path, 0o755)

            # Create project config directory
            project_config_dir = os.path.join(directory, project_name)
            os.makedirs(project_config_dir, exist_ok=True)
            create_init_file(project_config_dir, f"Created {project_name}/__init__.py")

            # Create settings directory and files
            settings_dir = os.path.join(project_config_dir, "settings")
            os.makedirs(settings_dir, exist_ok=True)
            create_init_file(settings_dir, f"Created {project_name}/settings/__init__.py")

            base_context = {"project_name": project_name, "app_names": []}
            create_file_from_template(
                os.path.join(settings_dir, "base.py"),
                "project/settings_base.j2",
                base_context,
                f"Created {project_name}/settings/base.py",
            )
            create_file_from_template(
                os.path.join(settings_dir, "development.py"),
                "project/settings_development.j2",
                {},
                f"Created {project_name}/settings/development.py",
            )
            create_file_from_template(
                os.path.join(settings_dir, "production.py"),
                "project/settings_production.j2",
                {},
                f"Created {project_name}/settings/production.py",
            )

            # Create project-level files
            urls_context = {"project_name": project_name, "django_version": DjangoHelper.DJANGO_VERSION}
            create_file_from_template(
                os.path.join(project_config_dir, "urls.py"),
                "project/urls.j2",
                urls_context,
                f"Created {project_name}/urls.py",
            )
            create_file_from_template(
                os.path.join(project_config_dir, "wsgi.py"),
                "project/wsgi.j2",
                {},
                f"Created {project_name}/wsgi.py",
            )
            create_file_from_template(
                os.path.join(project_config_dir, "asgi.py"),
                "project/asgi.j2",
                {},
                f"Created {project_name}/asgi.py",
            )

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
                ("apps.py", "app/apps.j2"),
                ("models.py", "app/models.j2"),
                ("views.py", "app/views.j2"),
                ("admin.py", "app/admin.j2"),
                ("urls.py", "app/urls.j2"),
                ("serializers.py", "app/serializers.j2"),
                ("routes.py", "app/routes.j2"),
                ("tests.py", "app/tests.j2"),
            ]

            for filename, template_path in app_files:
                create_file_from_template(
                    os.path.join(app_dir, filename),
                    template_path,
                    context,
                    f"Created {app_name}/{filename}",
                )

            # Create migrations directory and __init__.py
            migrations_dir = os.path.join(app_dir, "migrations")
            os.makedirs(migrations_dir, exist_ok=True)
            create_init_file(migrations_dir, f"Created {app_name}/migrations/__init__.py")

            return True

        except Exception as e:
            UIFormatter.print_error(f"Error creating Django app: {e}")
            return False
