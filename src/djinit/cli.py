"""
Main CLI orchestrator for djinit.
Coordinates between different managers to create a complete Django project.
"""

import os
from typing import Callable, List, Tuple

from djinit.scripts.cicd_config_generator import CICDConfigGenerator
from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.deployment_files_generator import DeploymentConfigGenerator
from djinit.scripts.files import FileManager
from djinit.scripts.project import ProjectManager
from djinit.scripts.secretkey_generator import generate_secret_command
from djinit.scripts.settings import SettingsManager


class Cli:
    def __init__(self, project_dir: str, project_name: str, primary_app: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.primary_app = primary_app
        self.app_names = app_names
        self.metadata = metadata
        self.project_root = os.path.join(os.getcwd(), project_dir)

        # Initialize managers
        self.project_manager = ProjectManager(project_dir, project_name, app_names, metadata)
        self.settings_manager = SettingsManager(self.project_root, project_name, app_names, metadata)
        self.file_manager = FileManager(self.project_root, project_name, app_names, metadata)
        self.deployment_manager = DeploymentConfigGenerator(self.project_root, project_name)
        self.cicd_manager = CICDConfigGenerator(self.project_root, project_name)

    def run_setup(self) -> bool:
        steps: List[Tuple[str, Callable[[], bool]]] = [
            ("Creating Django project", self.project_manager.create_project),
            ("Creating Django apps", self.project_manager.create_apps),
            ("Validating project structure", self.project_manager.validate_project_structure),
            ("Setting up project structure", self.settings_manager.create_settings_structure),
            ("Configuring base settings", self.settings_manager.update_base_settings),
            ("Configuring development settings", self.settings_manager.update_development_settings),
            ("Configuring production settings", self.settings_manager.update_production_settings),
            ("Creating utility files", self._create_utility_files),
            ("Setting up app URLs", self.file_manager.create_app_urls),
            ("Creating app serializers", self.file_manager.create_app_serializers),
            ("Creating app routes", self.file_manager.create_app_routes),
            ("Configuring comprehensive URLs", self.file_manager.update_project_urls),
            ("Updating WSGI configuration", self.file_manager.update_wsgi_file),
            ("Updating ASGI configuration", self.file_manager.update_asgi_file),
            ("Updating manage.py", self.file_manager.update_manage_py),
            ("Creating Justfile", self.deployment_manager.create_justfile),
            ("Creating Procfile", self.deployment_manager.create_procfile),
            ("Creating runtime.txt", lambda: self.deployment_manager.create_runtime_txt("3.13")),
            ("Creating CI/CD pipelines", self._create_cicd_pipelines),
        ]

        total_steps = len(steps)
        success = True

        # Create live progress display
        progress, task = UIFormatter.create_live_progress(description="Setup Progress", total_steps=total_steps)

        with progress:
            # Execute each step with progress tracking
            for step_number, (description, step_func) in enumerate(steps, 1):
                result = step_func()
                if not result:
                    success = False
                    UIFormatter.print_error(f"Step {step_number} failed: {description}")
                    break

                # Update the same progress bar
                progress.update(task, advance=1, description=f"Step {step_number}/{total_steps}")

        return success

    def _create_utility_files(self) -> bool:
        utility_steps = [
            self.file_manager.create_gitignore,
            self.file_manager.create_requirements,
            self.file_manager.create_readme,
            self.file_manager.create_env_file,
            lambda: self.file_manager.create_pyproject_toml(self.metadata),
        ]

        for step_func in utility_steps:
            result = step_func()
            if not result:
                return False

        UIFormatter.print_success("Created all utility files successfully!")
        return True

    def _create_cicd_pipelines(self) -> bool:
        if self.metadata.get("use_github_actions", True):
            result = self.cicd_manager.create_github_actions()
            if not result:
                return False

        if self.metadata.get("use_gitlab_ci", True):
            result = self.cicd_manager.create_gitlab_ci()
            if not result:
                return False

        return True

    def generate_secret_keys(self) -> bool:
        generate_secret_command()
        return True
