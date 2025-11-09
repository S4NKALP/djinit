"""
App management for djinit.
Handles creation of Django apps and updating settings.
"""

import os
<<<<<<< HEAD
=======
import subprocess
import sys
>>>>>>> origin/main
from typing import Optional

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.django_helper import DjangoHelper
from djinit.scripts.template_engine import template_engine
from djinit.utils import (
    calculate_app_module_path,
    create_file_with_content,
    create_init_file,
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
        # For predefined structure, check in apps/ directory
        if self._is_predefined_structure():
            app_path = os.path.join(self.current_dir, "apps", self.app_name)
        else:
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

<<<<<<< HEAD
        # If predefined structure detected (apps/ exists), scaffold nested layout using custom templates
        if self._is_predefined_structure():
            return self._create_predefined_app(os.path.join(self.current_dir, "apps"))
=======
        # Create app in the correct location
        # Use 'python -m django' instead of 'django-admin' for better compatibility
        with change_cwd(apps_base_dir):
            subprocess.run(
                [sys.executable, "-m", "django", "startapp", self.app_name], capture_output=True, text=True, check=True
            )
>>>>>>> origin/main

        # Otherwise, use standard flat app generation
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
        # For predefined structure, use "apps" as nested_dir
        if self._is_predefined_structure():
            app_module_path = f"apps.{self.app_name}"
        else:
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

    def _is_predefined_structure(self) -> bool:
        # Heuristic: presence of 'apps' directory at project root (where manage.py lives) and 'api' dir
        apps_dir = os.path.join(self.current_dir, "apps")
        api_dir = os.path.join(self.current_dir, "api")
        return os.path.isdir(apps_dir) and os.path.isdir(api_dir)

    def _create_predefined_app(self, apps_dir: str) -> bool:
        """Create an app following the predefined nested structure with custom templates."""
        app_dir = os.path.join(apps_dir, self.app_name)
        os.makedirs(app_dir, exist_ok=True)
        create_init_file(app_dir, f"Created apps/{self.app_name}/__init__.py")

        # apps.py using standard template
        apps_py_content = template_engine.render_template("base/apps.j2", {"app_name": self.app_name})
        create_file_with_content(
            os.path.join(app_dir, "apps.py"), apps_py_content, f"Created apps/{self.app_name}/apps.py"
        )

        # Compute names for generic templates
        model_class_name = "".join([part.capitalize() for part in self.app_name.split("_")])
        app_module = f"apps.{self.app_name}"

        # Subfolders
        subfolders = {
            "models": [(f"{self.app_name}.py", "predefined/apps/generic/models.j2")],
            "serializers": [(f"{self.app_name}_serializer.py", "predefined/apps/generic/serializers.j2")],
            "services": [(f"{self.app_name}_service.py", "predefined/apps/generic/services.j2")],
            "views": [(f"{self.app_name}_view.py", "predefined/apps/generic/views.j2")],
            "tests": [(f"test_{self.app_name}_api.py", "predefined/apps/generic/tests.j2")],
        }
        for folder, files in subfolders.items():
            folder_path = os.path.join(app_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            create_init_file(folder_path, f"Created apps/{self.app_name}/{folder}/__init__.py")
            for filename, tpl in files:
                content = template_engine.render_template(
                    tpl,
                    {"app_name": self.app_name, "app_module": app_module, "model_class_name": model_class_name},
                )
                create_file_with_content(
                    os.path.join(folder_path, filename),
                    content,
                    f"Created apps/{self.app_name}/{folder}/{filename}",
                )

        # urls.py at app root
        urls_content = template_engine.render_template(
            "predefined/apps/generic/urls.j2", {"app_name": self.app_name, "app_module": app_module}
        )
        create_file_with_content(
            os.path.join(app_dir, "urls.py"), urls_content, f"Created apps/{self.app_name}/urls.py"
        )

        # Add route include to api/v1/urls.py if present
        self._add_to_api_v1_urls(self.app_name)

        UIFormatter.print_success(f"Created Django app '{self.app_name}' with predefined structure in {apps_dir}")
        return True

    def _add_to_api_v1_urls(self, app_name: str) -> None:
        api_v1_urls = os.path.join(self.current_dir, "api", "v1", "urls.py")
        if not os.path.exists(api_v1_urls):
            return
        try:
            with open(api_v1_urls, encoding="utf-8") as f:
                content = f.read()

            import_line = "from django.urls import include, path"
            if import_line not in content:
                # ensure base import exists (fallback)
                content = import_line + "\n\n" + content

            include_stmt = f'path("{app_name}/", include("apps.{app_name}.urls")),'
            if include_stmt in content:
                # already present
                return

            # Insert into urlpatterns list before closing ]
            if "urlpatterns = [" in content:
                parts = content.split("urlpatterns = [", 1)
                before = parts[0]
                rest = parts[1]
                if "]" in rest:
                    idx = rest.rfind("]")
                    new_rest = rest[:idx]
                    # ensure newline and indentation
                    if not new_rest.endswith("\n"):
                        new_rest += "\n"
                    new_rest += f"    {include_stmt}\n" + rest[idx:]
                    content = before + "urlpatterns = [" + new_rest

            with open(api_v1_urls, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Non-fatal; leave API routes unchanged if edit fails
            return
