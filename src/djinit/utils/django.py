"""
Django helper module that replicates Django's startproject and startapp functionality.

This module provides functions to create Django projects and apps without requiring Django.
"""

import os

from djinit.core.config import DJANGO_VERSION
from djinit.utils.common import CommonUtils


class DjangoHelper:
    DJANGO_VERSION = DJANGO_VERSION

    @staticmethod
    def startproject(project_name: str, directory: str, unified: bool = False, metadata: dict = None) -> None:
        try:
            from djinit.utils.secretkey import generate_secret_key

            os.makedirs(directory, exist_ok=True)

            manage_py_path = os.path.join(directory, "manage.py")
            CommonUtils.create_file_from_template(
                manage_py_path, "project/manage.py-tpl", {"project_name": project_name}, "Created manage.py"
            )
            os.chmod(manage_py_path, 0o755)

            if unified:
                return

            project_config_dir = os.path.join(directory, project_name)
            CommonUtils.create_directory_with_init(project_config_dir, f"Created {project_name}/__init__.py")

            settings_dir = os.path.join(project_config_dir, "settings")
            CommonUtils.create_directory_with_init(settings_dir, f"Created {project_name}/settings/__init__.py")

            # Generate secret key for development
            secret_key = generate_secret_key()
            metadata = metadata or {}

            base_context = {
                "project_name": project_name,
                "app_names": [],
                "use_database_url": metadata.get("use_database_url", True),
                "database_type": metadata.get("database_type", "postgresql"),
            }

            dev_context = {"secret_key": secret_key}

            # Production context also needs database info
            prod_context = base_context.copy()

            settings_files = [
                ("base.py", "config/settings/base.py-tpl", base_context),
                ("development.py", "config/settings/development.py-tpl", dev_context),
                ("production.py", "config/settings/production.py-tpl", prod_context),
            ]
            CommonUtils.create_files_from_templates(settings_dir, settings_files, f"{project_name}/settings/")

            urls_context = {
                "url_type": "project",
                "project_name": project_name,
                "django_version": DjangoHelper.DJANGO_VERSION,
            }
            project_files = [
                ("urls.py", "config/urls.py-tpl", urls_context),
                ("wsgi.py", "config/wsgi.py-tpl", {"project_name": project_name}),
                ("asgi.py", "config/asgi.py-tpl", {"project_name": project_name}),
            ]
            CommonUtils.create_files_from_templates(project_config_dir, project_files, f"{project_name}/")

        except Exception as e:
            from djinit.utils.exceptions import DjinitError

            raise DjinitError(f"Error creating Django project: {e}", details=str(e)) from e

    @staticmethod
    def startapp(app_name: str, directory: str, app_module: str = None) -> bool:
        """Create a Django app with standard structure (empty files, no example code).

        Args:
            app_name: Name of the app to create
            directory: Directory where the app should be created
            app_module: Full module path (e.g., 'apps.users' for nested apps)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            app_dir = os.path.join(directory, app_name)
            os.makedirs(app_dir, exist_ok=True)

            # Prepare context
            app_config_name = app_name.title().replace("_", "")
            context = {
                "app_name": app_name,
                "app_config_name": app_config_name,
                "django_version": DjangoHelper.DJANGO_VERSION,
            }

            # Use provided app_module or default to app_name (path calculation handled by caller)
            if not app_module:
                app_module = app_name

            context["app_module"] = app_module

            # Create __init__.py
            CommonUtils.create_init_file(app_dir, f"Created {app_name}/__init__.py")

            # Create all standard Django app files (empty templates with basic structure)
            app_files = [
                ("apps.py", "components/apps.py-tpl", context),
                ("models.py", "components/models.py-tpl", context),
                ("views.py", "components/views.py-tpl", context),
                ("admin.py", "components/admin.py-tpl", context),
                ("serializers.py", "components/serializers.py-tpl", context),
                ("urls.py", "components/urls.py-tpl", context),
                ("tests.py", "components/tests.py-tpl", context),
            ]

            CommonUtils.create_files_from_templates(app_dir, app_files, f"{app_name}/")

            # Create migrations directory
            migrations_dir = os.path.join(app_dir, "migrations")
            CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

            return True

        except Exception as e:
            from djinit.utils.exceptions import DjinitError

            raise DjinitError(f"Error creating Django app: {e}", details=str(e)) from e
