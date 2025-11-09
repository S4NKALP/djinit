"""
Main CLI orchestrator for djinit.
Coordinates between different managers to create a complete Django project.
"""

import os
from typing import Callable, List, Tuple

from djinit.scripts.console_ui import UIFormatter
from djinit.scripts.files import FileManager
from djinit.scripts.project import ProjectManager
from djinit.scripts.secretkey_generator import generate_secret_command


class Cli:
    def __init__(self, project_dir: str, project_name: str, primary_app: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.primary_app = primary_app
        self.app_names = app_names
        self.metadata = metadata
<<<<<<< HEAD
        if project_dir == ".":  # handle '.' for current directory
=======
        # Handle '.' for current directory
        if project_dir == ".":
>>>>>>> origin/main
            self.project_root = os.getcwd()
        else:
            self.project_root = os.path.join(os.getcwd(), project_dir)

        self.project_manager = ProjectManager(project_dir, project_name, app_names, metadata)
        self.file_manager = FileManager(self.project_root, project_name, app_names, metadata)

    def run_setup(self) -> bool:
        # If predefined structure is enabled, adjust metadata defaults
        if self.metadata.get("predefined_structure"):
            # Default module name to 'config' for conventional layout
            self.metadata.setdefault("project_module_name", "config")
            # Ensure nested apps live under 'apps'
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            # Default apps for predefined structure
            if not self.app_names:
                self.app_names = ["users", "core"]
                # propagate to managers
                self.project_manager.app_names = self.app_names

        # If unified structure is enabled, adjust metadata defaults
        if self.metadata.get("unified_structure"):
            # For unified structure, module name is 'core'
            self.metadata.setdefault("project_module_name", "core")
            # Ensure nested apps live under 'apps'
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            # Default apps for unified structure (empty, apps/core and apps/api are created by default)
            if not self.app_names:
                self.app_names = []
                # propagate to managers
                self.project_manager.app_names = self.app_names

        steps: List[Tuple[str, Callable[[], bool]]] = []

        steps.append(("Creating Django project", self.project_manager.create_project))

        if self.metadata.get("unified_structure"):
            # Build unified structure
            steps.append(("Creating unified structure", self.file_manager.create_unified_structure))
        elif self.metadata.get("predefined_structure"):
            # Build custom tree and then inject apps into settings
            steps.append(("Creating predefined structure", self.file_manager.create_predefined_structure))
            steps.append(("Adding apps to settings", self.project_manager.add_apps_to_settings))
        else:
            steps.append(("Creating Django apps", self.project_manager.create_apps))
            steps.append(("Creating project URLs", self.file_manager.create_project_urls))

        steps.extend(
            [
                ("Validating project structure", self.project_manager.validate_project_structure),
                ("Creating utility files", self._create_utility_files),
                ("Creating Procfile", self.file_manager.create_procfile),
                ("Creating Justfile", self.file_manager.create_justfile),
                ("Creating runtime.txt", self.file_manager.create_runtime_txt),
                ("Creating CI/CD pipelines", self._create_cicd_pipelines),
            ]
        )

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
            result = self.file_manager.create_github_actions()
            if not result:
                return False

        if self.metadata.get("use_gitlab_ci", True):
            result = self.file_manager.create_gitlab_ci()
            if not result:
                return False

        return True

    def generate_secret_keys(self) -> bool:
        generate_secret_command()
        return True
