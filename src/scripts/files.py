"""
File management utilities for djinit.
Handles creation and modification of project files.
"""

import os

from src.scripts.template_engine import template_engine
from src.utils import change_cwd, create_file_with_content


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
            gitignore_content = template_engine.render_template("gitignore.j2", {})
            return create_file_with_content(
                ".gitignore",
                gitignore_content,
                "Created .gitignore file",
            )

    def create_requirements(self) -> bool:
        with change_cwd(self.project_root):
            requirements_content = template_engine.render_template("requirements.j2", {})
            return create_file_with_content(
                "requirements.txt",
                requirements_content,
                "Created requirements.txt with Django dependencies",
            )

    def create_readme(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name, "app_names": self.app_names}
            readme_content = template_engine.render_template("readme.j2", context)
            return create_file_with_content(
                "README.md",
                readme_content,
                "Created README.md file",
            )

    def create_env_file(self) -> bool:
        """Create .env.sample file with environment variables."""
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            env_content = template_engine.render_template("env_sample.j2", context)
            return create_file_with_content(
                ".env.sample",
                env_content,
                "Created .env.sample file with generated secret key",
            )

    def create_pyproject_toml(self, metadata: dict) -> bool:
        with change_cwd(self.project_root):
            context = {"package_name": metadata["package_name"], "project_name": self.project_name}
            pyproject_content = template_engine.render_template("pyproject_toml.j2", context)
            return create_file_with_content(
                "pyproject.toml",
                pyproject_content,
                "Created pyproject.toml file for uv",
            )

    def create_app_urls(self) -> bool:
        apps_base_dir = self.project_root
        if self.metadata.get("nested_apps") and self.metadata.get("nested_dir"):
            apps_base_dir = os.path.join(self.project_root, self.metadata.get("nested_dir"))

        for app_name in self.app_names:
            app_path = os.path.join(apps_base_dir, app_name)
            with change_cwd(app_path):
                context = {"app_name": app_name}
                urls_content = template_engine.render_template("app_urls.j2", context)
                create_file_with_content(
                    "urls.py",
                    urls_content,
                    f"Created {app_name}/urls.py",
                    should_format=True,
                )
        return True

    def update_project_urls(self) -> bool:
        with change_cwd(self.project_configs):
            nested = bool(self.metadata.get("nested_apps"))
            nested_dir = self.metadata.get("nested_dir")
            effective_app_modules = [
                f"{nested_dir}.{name}" if nested and nested_dir else name for name in self.app_names
            ]
            context = {
                "project_name": self.project_name,
                "app_names": effective_app_modules,
            }
            urls_content = template_engine.render_template("project_urls.j2", context)
            result = create_file_with_content(
                "urls.py",
                urls_content,
                "Updated project urls.py with comprehensive URL configuration",
                should_format=True,
            )
            return result

    def update_wsgi_file(self) -> bool:
        with change_cwd(self.project_configs):
            wsgi_content = template_engine.render_template("wsgi.j2", {})
            return create_file_with_content(
                "wsgi.py",
                wsgi_content,
                "Updated wsgi.py with custom configuration",
                should_format=True,
            )

    def update_asgi_file(self) -> bool:
        with change_cwd(self.project_configs):
            asgi_content = template_engine.render_template("asgi.j2", {})
            return create_file_with_content(
                "asgi.py",
                asgi_content,
                "Updated asgi.py with custom configuration",
                should_format=True,
            )

    def update_manage_py(self) -> bool:
        """Update manage.py with custom configuration."""
        with change_cwd(self.project_root):
            manage_content = template_engine.render_template("manage_py.j2", {})
            return create_file_with_content(
                "manage.py",
                manage_content,
                "Updated manage.py with custom configuration",
                should_format=True,
            )
