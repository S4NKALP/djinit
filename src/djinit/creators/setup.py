import os
from typing import Callable, List, Tuple

from djinit.creators.architectures import ARCHITECTURE_HANDLERS
from djinit.creators.files import FileCreator
from djinit.creators.project import ProjectCreator
from djinit.ui.console import UIFormatter
from djinit.utils.common import CommonUtils


class SetupCreator:
    """
    Orchestrator for creating a complete Django project.
    Combines ProjectCreator and FileCreator to set up the environment.
    """

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

        self.project_creator = ProjectCreator(project_dir, project_name, app_names, metadata)
        self.file_creator = FileCreator(self.project_root, project_name, app_names, metadata)

    def _normalize_metadata(self) -> None:
        """Normalize metadata and app names based on structure type."""
        arch = self.metadata.get("architecture")
        if arch in ARCHITECTURE_HANDLERS:
            if arch == "lightweight":
                self.metadata.setdefault("nested_apps", False)
                if not self.app_names:
                    self.app_names = []
            else:
                self.metadata.setdefault("project_module_name", "config")
                self.metadata.setdefault("nested_apps", True)
                self.metadata.setdefault("nested_dir", "apps")
                if not self.app_names:
                    defaults = {
                        "modular_monolith": ["accounts", "core"],
                        "service_layer": ["products", "core"],
                        "fullstack_htmx": ["dashboard"],
                        "ddd": ["orders", "core"],
                        "clean_architecture": ["users", "core"],
                        "multi_tenant": ["projects"],
                    }
                    self.app_names = defaults.get(arch, ["core"])
            self.project_creator.app_names = self.app_names
            self.file_creator.app_names = self.app_names
            # Update module name on creators
            if self.metadata.get("project_module_name"):
                self.project_creator.module_name = self.metadata["project_module_name"]
                self.file_creator.module_name = self.metadata["project_module_name"]
                self.file_creator.project_configs = os.path.join(
                    self.project_root, self.metadata["project_module_name"]
                )

        elif self.metadata.get("predefined_structure"):
            self.metadata.setdefault("project_module_name", "config")
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            if not self.app_names:
                self.app_names = ["users", "core"]
                self.project_creator.app_names = self.app_names
                self.file_creator.app_names = self.app_names

        elif self.metadata.get("unified_structure"):
            self.metadata.setdefault("project_module_name", "core")
            self.metadata.setdefault("nested_apps", True)
            self.metadata.setdefault("nested_dir", "apps")
            if not self.app_names:
                self.app_names = []
                self.project_creator.app_names = self.app_names
                self.file_creator.app_names = self.app_names

        elif self.metadata.get("single_structure"):
            self.metadata.setdefault("nested_apps", False)
            if not self.app_names:
                self.app_names = []
                self.project_creator.app_names = self.app_names
                self.file_creator.app_names = self.app_names

    def create(self) -> bool:
        """Run the full setup process."""
        self._normalize_metadata()

        steps: List[Tuple[str, Callable[[], None]]] = []

        steps.append(("Creating Django project", self.project_creator.create_project))

        arch = self.metadata.get("architecture")
        if arch in ARCHITECTURE_HANDLERS:
            handler = ARCHITECTURE_HANDLERS[arch]
            steps.append(
                (
                    f"Creating {arch.replace('_', ' ').title()} structure",
                    lambda: handler.scaffold_project(self.file_creator),
                )
            )
            if arch == "multi_tenant":

                def add_tenancy_and_apps():
                    base_settings_path = CommonUtils.get_base_settings_path(
                        self.project_root, self.file_creator.module_name
                    )
                    content = CommonUtils.read_base_settings(self.project_root, self.file_creator.module_name)
                    if content and "tenancy.apps.TenancyConfig" not in content:
                        updated = CommonUtils.insert_apps_into_user_defined_apps(
                            content, ["tenancy.apps.TenancyConfig"]
                        )
                        if updated:
                            content = updated

                    if content and "tenancy.middleware.TenantMiddleware" not in content:
                        content = content.replace(
                            '"django.contrib.auth.middleware.AuthenticationMiddleware",',
                            '"django.contrib.auth.middleware.AuthenticationMiddleware",\n    "tenancy.middleware.TenantMiddleware",',
                        )

                    if content:
                        with open(base_settings_path, "w", encoding="utf-8") as f:
                            f.write(content)
                    self.project_creator.add_apps_to_settings()

                steps.append(("Adding apps to settings", add_tenancy_and_apps))
            elif arch != "lightweight":
                steps.append(("Adding apps to settings", self.project_creator.add_apps_to_settings))

            if arch != "lightweight":

                def register_initial_urls():
                    for app in self.app_names:
                        self.file_creator.add_app_url_route(app, f"apps.{app}")

                steps.append(("Configuring app URLs", register_initial_urls))

        elif self.metadata.get("unified_structure"):
            steps.append(("Creating unified structure", self.file_creator.create_unified_structure))
        elif self.metadata.get("single_structure"):
            steps.append(("Creating single folder structure", self.file_creator.create_single_structure))
        elif self.metadata.get("predefined_structure"):
            steps.append(("Creating predefined structure", self.file_creator.create_predefined_structure))
            steps.append(("Adding apps to settings", self.project_creator.add_apps_to_settings))
        else:
            steps.append(("Creating Django apps", self.project_creator.create_apps))
            steps.append(("Creating project URLs", self.file_creator.create_project_urls))
            steps.append(("Creating shared module", self.file_creator.create_standard_shared))

        steps.extend(
            [
                ("Validating project structure", self.project_creator.validate_project_structure),
                ("Creating utility files", self._create_utility_files),
                ("Creating Procfile", self.file_creator.create_procfile),
                ("Creating Justfile", self.file_creator.create_justfile),
                ("Creating runtime.txt", self.file_creator.create_runtime_txt),
                ("Creating CI/CD pipelines", self._create_cicd_pipelines),
            ]
        )

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
            self.file_creator.create_gitignore,
            self.file_creator.create_requirements,
            self.file_creator.create_readme,
            self.file_creator.create_env_file,
            self.file_creator.create_djinit_config,
            self.file_creator.create_dockerfile,
            self.file_creator.create_docker_compose,
            self.file_creator.create_passenger_wsgi,
            self.file_creator.create_dockerignore,
            lambda: self.file_creator.create_pyproject(self.metadata),
        ]

        for step_func in utility_steps:
            step_func()

        if self.metadata.get("use_vite", False):
            self.file_creator.create_vite_config()

        UIFormatter.print_success("Created all utility files successfully!")

    def _create_cicd_pipelines(self) -> None:
        if self.metadata.get("use_github_actions", True):
            self.file_creator.create_github_actions()

        if self.metadata.get("use_gitlab_ci", True):
            self.file_creator.create_gitlab_ci()
