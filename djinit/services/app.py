"""
App management for djinit.
Handles creation of Django apps and updating settings.
"""

import os
from typing import Optional

from djinit.ui.console import UIFormatter
from djinit.utils.common import (
    calculate_app_module_path,
    create_directory_with_init,
    create_file_from_template,
    create_init_file,
    detect_nested_structure_from_settings,
    extract_existing_apps,
    find_project_dir,
    find_settings_path,
    get_djinit_config,
    insert_apps_into_user_defined_apps,
    is_django_project,
)
from djinit.utils.django import DjangoHelper


class AppManager:
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.current_dir = os.getcwd()
        self.manage_py_path = os.path.join(self.current_dir, "manage.py")
        self.config = get_djinit_config(self.current_dir)
        self._project_structure_cache = None

    def create_app(self) -> bool:
        if not self._is_django_project():
            UIFormatter.print_error(
                "Not in a Django project directory. Please run this command from your Django project root."
            )
            return False

        if self._is_restricted_structure():
            UIFormatter.print_error("The 'app' command is not supported for Unified or Single Folder structures.")
            UIFormatter.print_info(
                "Please add new apps manually by creating the necessary files and updating settings."
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
            _, _, apps_base_dir = self._get_project_structure()
            app_path = os.path.join(apps_base_dir, self.app_name)
        return os.path.exists(app_path)

    def _create_django_app(self) -> bool:
        if not os.path.exists(self.manage_py_path):
            UIFormatter.print_error("Could not find manage.py file in project root")
            return False

        if self._is_predefined_structure():
            return self._create_predefined_app(os.path.join(self.current_dir, "apps"))

        _, _, apps_base_dir = self._get_project_structure()
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

        if self._is_predefined_structure():
            app_module_path = f"apps.{self.app_name}"
        else:
            is_nested, nested_dir, _ = self._get_project_structure()
            app_module_path = calculate_app_module_path(self.app_name, is_nested, nested_dir)

        existing_apps = extract_existing_apps(content)
        if app_module_path in existing_apps:
            UIFormatter.print_success(f"App '{app_module_path}' already configured in USER_DEFINED_APPS")
            return True

        if "USER_DEFINED_APPS" not in content:
            UIFormatter.print_error("Could not find USER_DEFINED_APPS section in base.py")
            return False

        updated_content = insert_apps_into_user_defined_apps(content, [app_module_path])
        if not updated_content:
            return False

        with open(base_settings_path, "w") as f:
            f.write(updated_content)

        UIFormatter.print_success(f"Added '{app_module_path}' to USER_DEFINED_APPS in base.py")
        return True

    def _get_project_structure(self) -> tuple[bool, Optional[str], str]:
        """Get project structure with caching to avoid repeated detection."""
        if self._project_structure_cache is None:
            if self.config:
                apps_config = self.config.get("apps", {})
                nested = apps_config.get("nested", False)
                nested_dir = apps_config.get("nested_dir")

                # Determine base dir for apps
                if nested and nested_dir:
                    apps_base_dir = os.path.join(self.current_dir, nested_dir)
                else:
                    apps_base_dir = self.current_dir

                self._project_structure_cache = (nested, nested_dir, apps_base_dir)
            else:
                # Fallback to old detection method
                project_dir, settings_base_path = find_project_dir(self.current_dir)

                if project_dir is None:
                    self._project_structure_cache = (False, None, self.current_dir)
                else:
                    self._project_structure_cache = detect_nested_structure_from_settings(
                        settings_base_path, self.current_dir
                    )
        return self._project_structure_cache

    def _is_predefined_structure(self) -> bool:
        if self.config:
            return self.config.get("structure", {}).get("predefined", False)

        apps_dir = os.path.join(self.current_dir, "apps")
        api_dir = os.path.join(self.current_dir, "api")
        return os.path.isdir(apps_dir) and os.path.isdir(api_dir)

    def _is_restricted_structure(self) -> bool:
        """Check if the project structure is Unified or Single Folder."""
        if self.config:
            structure = self.config.get("structure", {})
            return structure.get("unified", False) or structure.get("single", False)

        # Check for Unified structure (apps/api exists)
        if os.path.isdir(os.path.join(self.current_dir, "apps", "api")):
            return True

        # Check for Predefined structure (apps/ exists but not apps/api)
        if os.path.isdir(os.path.join(self.current_dir, "apps")):
            return False

        # Check for Single Folder structure (models/ and api/ exist in project dir)
        project_dir, _ = find_project_dir(self.current_dir)
        if project_dir:
            has_models = os.path.isdir(os.path.join(project_dir, "models"))
            has_api = os.path.isdir(os.path.join(project_dir, "api"))
            if has_models and has_api:
                return True

        return False

    def _create_predefined_app(self, apps_dir: str) -> bool:
        """Create an app following the predefined nested structure with custom templates."""
        app_dir = os.path.join(apps_dir, self.app_name)
        os.makedirs(app_dir, exist_ok=True)
        create_init_file(app_dir, f"Created apps/{self.app_name}/__init__.py")

        model_class_name = "".join([part.capitalize() for part in self.app_name.split("_")])
        app_module = f"apps.{self.app_name}"
        base_context = {"app_name": self.app_name, "app_module": app_module, "model_class_name": model_class_name}

        create_file_from_template(
            os.path.join(app_dir, "apps.py"),
            "components/apps.j2",
            {"app_name": self.app_name},
            f"Created apps/{self.app_name}/apps.py",
        )

        subfolders = {
            "models": [(f"{self.app_name}.py", "presets/predefined/apps/generic/models.j2")],
            "serializers": [(f"{self.app_name}_serializer.py", "presets/predefined/apps/generic/serializers.j2")],
            "services": [(f"{self.app_name}_service.py", "presets/predefined/apps/generic/services.j2")],
            "views": [(f"{self.app_name}_view.py", "presets/predefined/apps/generic/views.j2")],
            "tests": [(f"test_{self.app_name}_api.py", "presets/predefined/apps/generic/tests.j2")],
        }
        for folder, files in subfolders.items():
            folder_path = os.path.join(app_dir, folder)
            create_directory_with_init(folder_path, f"Created apps/{self.app_name}/{folder}/__init__.py")
            for filename, template in files:
                file_path = os.path.join(folder_path, filename)
                create_file_from_template(
                    file_path, template, base_context, f"Created apps/{self.app_name}/{folder}/{filename}"
                )

        create_file_from_template(
            os.path.join(app_dir, "urls.py"),
            "presets/predefined/apps/generic/urls.j2",
            {"app_name": self.app_name, "app_module": app_module},
            f"Created apps/{self.app_name}/urls.py",
        )

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
                return

            if "urlpatterns = [" in content:
                parts = content.split("urlpatterns = [", 1)
                before = parts[0]
                rest = parts[1]
                if "]" in rest:
                    idx = rest.rfind("]")
                    new_rest = rest[:idx]
                    if not new_rest.endswith("\n"):
                        new_rest += "\n"
                    new_rest += f"    {include_stmt}\n" + rest[idx:]
                    content = before + "urlpatterns = [" + new_rest

            with open(api_v1_urls, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            return
