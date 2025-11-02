"""
File management utilities for djinit.
Handles creation and modification of project files.
"""

import os

from djinit.scripts.template_engine import template_engine
from djinit.utils import (
    calculate_app_module_paths,
    change_cwd,
    create_file_with_content,
)


class FileManager:
    def __init__(self, project_root: str, project_name: str, app_names: list, metadata: dict):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        self.project_configs = os.path.join(project_root, project_name)
        self.settings_folder = os.path.join(self.project_configs, "settings")
        self.settings_file = os.path.join(self.project_configs, "settings.py")

    def create_gitignore(self) -> bool:
        with change_cwd(self.project_root):
            gitignore_content = template_engine.render_template("shared/gitignore.j2", {})
            return create_file_with_content(
                ".gitignore",
                gitignore_content,
                "Created .gitignore file",
            )

    def create_requirements(self) -> bool:
        with change_cwd(self.project_root):
            context = {"use_database_url": self.metadata.get("use_database_url", True)}
            requirements_content = template_engine.render_template("shared/requirements.j2", context)
            return create_file_with_content(
                "requirements.txt",
                requirements_content,
                "Created requirements.txt with Django dependencies",
            )

    def create_readme(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name, "app_names": self.app_names}
            readme_content = template_engine.render_template("shared/readme.j2", context)
            return create_file_with_content(
                "README.md",
                readme_content,
                "Created README.md file",
            )

    def create_env_file(self) -> bool:
        """Create .env.sample file with environment variables."""
        with change_cwd(self.project_root):
            context = {
                "project_name": self.project_name,
                "use_database_url": self.metadata.get("use_database_url", True),
            }
            env_content = template_engine.render_template("shared/env_sample.j2", context)
            return create_file_with_content(
                ".env.sample",
                env_content,
                "Created .env.sample file with generated secret key",
            )

    def create_pyproject_toml(self, metadata: dict) -> bool:
        with change_cwd(self.project_root):
            context = {"package_name": metadata["package_name"], "project_name": self.project_name}
            pyproject_content = template_engine.render_template("shared/pyproject_toml.j2", context)
            return create_file_with_content(
                "pyproject.toml",
                pyproject_content,
                "Created pyproject.toml file for uv",
            )

    def create_project_urls(self) -> bool:
        """Create project urls.py using project_urls.j2 template (replaces update_project_urls)."""
        with change_cwd(self.project_configs):
            effective_app_modules = calculate_app_module_paths(self.app_names, self.metadata)
            context = {
                "project_name": self.project_name,
                "app_names": effective_app_modules,
            }
            urls_content = template_engine.render_template("project/project_urls.j2", context)
            result = create_file_with_content(
                "urls.py",
                urls_content,
                "Created project urls.py with comprehensive URL configuration",
                should_format=True,
            )
            return result

    def create_justfile(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            justfile_content = template_engine.render_template("shared/justfile.j2", context)
            create_file_with_content(
                "justfile",
                justfile_content,
                "Created justfile with Django development tasks",
            )
        return True

    def create_procfile(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            procfile_content = template_engine.render_template("shared/procfile.j2", context)
            create_file_with_content(
                "Procfile",
                procfile_content,
                "Created Procfile with Gunicorn configuration",
            )
        return True

    def create_runtime_txt(self) -> bool:
        with change_cwd(self.project_root):
            context = {"python_version": "3.13"}
            runtime_content = template_engine.render_template("shared/runtime_txt.j2", context)
            create_file_with_content(
                "runtime.txt",
                runtime_content,
                "Created runtime.txt with Python version specification",
            )
        return True

    def create_github_actions(self) -> bool:
        with change_cwd(self.project_root):
            github_dir = os.path.join(self.project_root, ".github", "workflows")
            os.makedirs(github_dir, exist_ok=True)

            context = {"project_name": self.project_name}
            workflow_content = template_engine.render_template("shared/github_actions_ci.j2", context)
            workflow_file = os.path.join(github_dir, "ci.yml")
            create_file_with_content(
                workflow_file,
                workflow_content,
                "Created Github Actions workflow (ci.yml)",
            )
        return True

    def create_gitlab_ci(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            gitlab_ci_content = template_engine.render_template("shared/gitlab_ci.j2", context)
            create_file_with_content(
                ".gitlab-ci.yml",
                gitlab_ci_content,
                "Created GitLab CI configuration (.gitlab-ci.yml)",
            )
        return True
