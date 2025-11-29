"""
Main CLI orchestrator for djinit.
Coordinates between different managers to create a complete Django project.
"""

import os
from typing import Callable, List, Tuple

from djinit.services.files import FileManager
from djinit.services.project import ProjectManager
from djinit.ui.console import UIFormatter


class Cli:
    def __init__(self, project_dir: str, project_name: str, primary_app: str, app_names: list, metadata: dict):
        self.project_dir = project_dir
        self.project_name = project_name
        self.primary_app = primary_app
        self.app_names = app_names
        self.metadata = metadata
        if project_dir == ".":
            self.project_root = os.getcwd()
        else:
            self.project_root = os.path.join(os.getcwd(), project_dir)

        self.project_manager = ProjectManager(project_dir, project_name, app_names, metadata)
        self.file_manager = FileManager(self.project_root, project_name, app_names, metadata)

    def _normalize_metadata(self) -> None:
        """Normalize metadata and app names based on structure type."""
        if self.metadata.get("predefined_structure"):
            self.metadata.setdefault("project_module_name", "config")
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            if not self.app_names:
                self.app_names = ["users", "core"]
                self.project_manager.app_names = self.app_names

        elif self.metadata.get("unified_structure"):
            self.metadata.setdefault("project_module_name", "core")
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            if not self.app_names:
                self.app_names = []
                self.project_manager.app_names = self.app_names

        elif self.metadata.get("single_structure"):
            self.metadata.setdefault("nested_apps", False)
            if not self.app_names:
                self.app_names = []
                self.project_manager.app_names = self.app_names

    def run_setup(self) -> bool:
        self._normalize_metadata()

        steps: List[Tuple[str, Callable[[], None]]] = []

        steps.append(("Creating Django project", self.project_manager.create_project))

        if self.metadata.get("unified_structure"):
            steps.append(("Creating unified structure", self.file_manager.create_unified_structure))
        elif self.metadata.get("single_structure"):
            steps.append(("Creating single folder structure", self.file_manager.create_single_structure))
        elif self.metadata.get("predefined_structure"):
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
        total_steps = len(steps)
        success = True

        progress, task = UIFormatter.create_live_progress(description="Setup Progress", total_steps=total_steps)

        try:
            with progress:
                for step_number, (_, step_func) in enumerate(steps, 1):
                    step_func()
                    progress.update(task, advance=1, description=f"Step {step_number}/{total_steps}")

        except Exception as e:
            success = False
            UIFormatter.handle_exception(e)

        return success

    def _create_utility_files(self) -> None:
        utility_steps = [
            self.file_manager.create_gitignore,
            self.file_manager.create_requirements,
            self.file_manager.create_readme,
            self.file_manager.create_env_file,
            self.file_manager.create_djinit_config,
            lambda: self.file_manager.create_pyproject_toml(self.metadata),
        ]

        for step_func in utility_steps:
            step_func()

        UIFormatter.print_success("Created all utility files successfully!")

    def _create_cicd_pipelines(self) -> None:
        if self.metadata.get("use_github_actions", True):
            self.file_manager.create_github_actions()

        if self.metadata.get("use_gitlab_ci", True):
            self.file_manager.create_gitlab_ci()
