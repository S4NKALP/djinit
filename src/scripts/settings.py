"""
Settings management for djinit.
Handles creation and configuration of Django settings files.
"""

import os

from src.scripts.console_ui import UIFormatter
from src.scripts.secretkey_generator import generate_secret_key
from src.scripts.template_engine import template_engine
from src.utils import change_cwd, create_file_with_content


class SettingsManager:
    def __init__(self, project_root: str, project_name: str, app_names: list, metadata: dict):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        self.project_configs = os.path.join(project_root, project_name)
        self.settings_folder = os.path.join(self.project_configs, "settings")
        self.settings_file = os.path.join(self.project_configs, "settings.py")
        self.secret_key = generate_secret_key(50)

    def create_settings_structure(self) -> bool:
        # Change to project configs directory
        with change_cwd(self.project_configs):
            # Create settings folder
            os.makedirs("settings", exist_ok=True)

            # Move settings.py to settings/base.py
            if os.path.exists(self.settings_file):
                os.rename(self.settings_file, os.path.join(self.settings_folder, "base.py"))

            # Create __init__.py files
            with change_cwd(self.settings_folder):
                open("__init__.py", "a").close()
                open("development.py", "a").close()
                open("production.py", "a").close()

        UIFormatter.print_success("Created Django settings folder structure")
        return True

    def update_base_settings(self) -> bool:
        with change_cwd(self.settings_folder):
            nested = bool(self.metadata.get("nested_apps"))
            nested_dir = self.metadata.get("nested_dir")
            effective_app_names = [f"{nested_dir}.{name}" if nested and nested_dir else name for name in self.app_names]
            context = {
                "project_name": self.project_name,
                "app_names": effective_app_names,
            }
            base_content = template_engine.render_template("settings_base.j2", context)
            return create_file_with_content(
                "base.py",
                base_content,
                "Updated settings/base.py with comprehensive configuration",
                should_format=True,
            )

    def update_development_settings(self) -> bool:
        """Update development.py with development-specific settings."""
        with change_cwd(self.settings_folder):
            context = {"secret_key": self.secret_key}
            dev_content = template_engine.render_template("settings_development.j2", context)
            return create_file_with_content(
                "development.py",
                dev_content,
                "Updated settings/development.py",
                should_format=True,
            )

    def update_production_settings(self) -> bool:
        """Update production.py with production-specific settings."""
        with change_cwd(self.settings_folder):
            context = {"use_database_url": self.metadata.get("use_database_url", True)}
            prod_content = template_engine.render_template("settings_production.j2", context)
            return create_file_with_content(
                "production.py",
                prod_content,
                "Updated settings/production.py",
                should_format=True,
            )
