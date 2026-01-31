"""
App management for djinit.
Handles creation of Django apps and updating settings.
"""

import os
from typing import Optional

from djinit.core.base import BaseService
from djinit.ui.console import UIFormatter
from djinit.utils.common import CommonUtils
from djinit.utils.django import DjangoHelper


class AppCreator(BaseService):
    def __init__(self, app_name: str):
        super().__init__()
        self.app_name = app_name
        self.current_dir = os.getcwd()
        self.manage_py_path = os.path.join(self.current_dir, "manage.py")
        self.config = CommonUtils.get_djinit_config(self.current_dir)
        self._project_structure_cache = None

    def create_app(self) -> bool:
        if not self._is_django_project():
            UIFormatter.print_error(
                "Not in a Django project directory. Please run this command from your Django project root."
            )
            return False

        # Check structure type
        structure_type = self._get_structure_type()

        if structure_type in ["unified", "single"]:
            UIFormatter.print_warning(
                f"Creating apps in {structure_type} structure. "
                "Note: You'll need to manually organize your code within the existing structure."
            )

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
        return CommonUtils.is_django_project(self.current_dir)

    def _get_structure_type(self) -> str:
        """Determine the project structure type."""
        if self.config:
            structure = self.config.get("structure", {})
            if structure.get("unified"):
                return "unified"
            elif structure.get("single"):
                return "single"
            elif structure.get("predefined"):
                return "predefined"
            else:
                return "standard"

        # Fallback: detect from filesystem
        if self._is_predefined_structure():
            return "predefined"
        if self._is_restricted_structure():
            # Try to distinguish between unified and single
            if os.path.isdir(os.path.join(self.current_dir, "apps", "api")):
                return "unified"
            return "single"
        return "standard"

    def _calculate_app_module_path(self, structure_type: str) -> str:
        """Calculate the module path for the app based on structure type."""
        if structure_type == "unified":
            # Unified structure: apps are not separate, return app name within apps module
            # But actually in unified, we don't create separate apps - the structure is different
            # For now, return a path that makes sense: apps.{appname}
            return f"apps.{self.app_name}"
        elif structure_type == "single":
            # Single structure: app is within the single module
            module_name = self.config.get("project_name") if self.config else self.app_name
            return f"{module_name}.{self.app_name}"
        elif structure_type == "predefined":
            # Predefined: apps are in apps/ directory
            return f"apps.{self.app_name}"
        else:
            # Standard: may be nested or not
            is_nested, nested_dir, _ = self._get_project_structure()
            return CommonUtils.calculate_app_module_path(self.app_name, is_nested, nested_dir)

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

        is_nested, nested_dir, apps_base_dir = self._get_project_structure()

        # Calculate app_module based on project structure
        if is_nested and nested_dir:
            # Normalize nested_dir (replace / with . for module path)
            module_base = nested_dir.replace(os.path.sep, ".")
            app_module = f"{module_base}.{self.app_name}"
        else:
            app_module = self.app_name

        success = DjangoHelper.startapp(self.app_name, apps_base_dir, app_module)
        if success:
            UIFormatter.print_success(f"Created Django app '{self.app_name}' in {apps_base_dir}")
        else:
            UIFormatter.print_error(f"Failed to create Django app '{self.app_name}'")
        return success

    def _add_to_installed_apps(self) -> bool:
        structure_type = self._get_structure_type()

        # Find settings directory based on structure type
        if structure_type == "unified":
            settings_path = os.path.join(self.current_dir, "core", "settings")
        elif structure_type == "single":
            # For single structure, find the module name from config or detect it
            module_name = self.config.get("project_name") if self.config else None
            if not module_name:
                # Fallback: find settings directory
                settings_path = CommonUtils.find_settings_path(self.current_dir)
            else:
                settings_path = os.path.join(self.current_dir, module_name, "settings")
        else:
            # Standard or predefined structure
            settings_path = CommonUtils.find_settings_path(self.current_dir)

        if not settings_path or not os.path.exists(settings_path):
            UIFormatter.print_error("Could not find Django settings directory")
            return False

        base_settings_path = os.path.join(settings_path, "base.py")
        if not os.path.exists(base_settings_path):
            UIFormatter.print_error("Could not find base.py settings file")
            return False

        with open(base_settings_path) as f:
            content = f.read()

        # Calculate the app module path based on structure
        app_module_path = self._calculate_app_module_path(structure_type)

        # Use full AppConfig path to properly support nested apps
        # e.g. apps.users -> apps.users.apps.UsersConfig
        app_config_name = self.app_name.title().replace("_", "")
        full_app_config = f"{app_module_path}.apps.{app_config_name}Config"

        # We'll check if either the module path or the full config path exists
        # but we'll prefer adding the full config path

        existing_apps = CommonUtils.extract_existing_apps(content)

        # Check if full config is already there
        if full_app_config in existing_apps:
            UIFormatter.print_success(f"App '{full_app_config}' already configured in USER_DEFINED_APPS")
            return True

        # Check if legacy module path is there, if so, upgrade it
        if app_module_path in existing_apps:
            UIFormatter.print_info(f"Upgrading app configuration from '{app_module_path}' to '{full_app_config}'...")
            updated_content = CommonUtils.replace_app_in_user_defined_apps(content, app_module_path, full_app_config)

            if updated_content:
                with open(base_settings_path, "w") as f:
                    f.write(updated_content)
                UIFormatter.print_success(f"Upgraded '{app_module_path}' to '{full_app_config}' in USER_DEFINED_APPS")
                return True
            else:
                UIFormatter.print_error(f"Failed to upgrade app '{app_module_path}'")
                return False

        if "USER_DEFINED_APPS" not in content:
            UIFormatter.print_error("Could not find USER_DEFINED_APPS section in base.py")
            return False

        updated_content = CommonUtils.insert_apps_into_user_defined_apps(content, [full_app_config])
        if not updated_content:
            return False

        with open(base_settings_path, "w") as f:
            f.write(updated_content)

        UIFormatter.print_success(f"Added '{full_app_config}' to USER_DEFINED_APPS in base.py")
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
                project_dir, settings_base_path = CommonUtils.find_project_dir(self.current_dir)

                if project_dir is None:
                    self._project_structure_cache = (False, None, self.current_dir)
                else:
                    self._project_structure_cache = CommonUtils.detect_nested_structure_from_settings(
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
        project_dir, _ = CommonUtils.find_project_dir(self.current_dir)
        if project_dir:
            has_models = os.path.isdir(os.path.join(project_dir, "models"))
            has_api = os.path.isdir(os.path.join(project_dir, "api"))
            if has_models and has_api:
                return True

        return False

    def _create_predefined_app(self, apps_dir: str) -> bool:
        """Create an app following the predefined structure with standard Django files."""
        app_module = f"apps.{self.app_name}"

        # Use DjangoHelper.startapp to create standard Django app structure
        success = DjangoHelper.startapp(self.app_name, apps_dir, app_module)

        if success:
            UIFormatter.print_success(f"Created Django app '{self.app_name}' with predefined structure in {apps_dir}")
        else:
            UIFormatter.print_error(f"Failed to create Django app '{self.app_name}'")

        return success

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
