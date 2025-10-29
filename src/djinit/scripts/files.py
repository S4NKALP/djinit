"""
File management utilities for djinit.
Handles creation and modification of project files.
"""

import os

from djinit.scripts.template_engine import template_engine
from djinit.utils import change_cwd, create_file_with_content


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
            context = {"use_database_url": self.metadata.get("use_database_url", True)}
            requirements_content = template_engine.render_template("requirements.j2", context)
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
            context = {
                "project_name": self.project_name,
                "use_database_url": self.metadata.get("use_database_url", True),
            }
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

    def _get_apps_base_dir(self) -> str:
        """Get the base directory for apps based on project structure."""
        if self.metadata.get("nested_apps") and self.metadata.get("nested_dir"):
            return os.path.join(self.project_root, self.metadata.get("nested_dir"))
        return self.project_root

    def _create_app_file(self, apps_base_dir: str, app_name: str, template_name: str, filename: str) -> None:
        """Helper method to create app files."""
        app_path = os.path.join(apps_base_dir, app_name)
        with change_cwd(app_path):
            context = {"app_name": app_name}
            content = template_engine.render_template(template_name, context)
            create_file_with_content(
                filename,
                content,
                f"Created {app_name}/{filename}",
                should_format=True,
            )

    def create_app_urls(self) -> bool:
        apps_base_dir = self._get_apps_base_dir()
        for app_name in self.app_names:
            self._create_app_file(apps_base_dir, app_name, "app_urls.j2", "urls.py")
        return True

    def create_app_serializers(self) -> bool:
        """Create serializers.py file for each app."""
        apps_base_dir = self._get_apps_base_dir()
        for app_name in self.app_names:
            self._create_app_file(apps_base_dir, app_name, "serializers.j2", "serializers.py")
        return True

    def create_app_routes(self) -> bool:
        """Create routes.py file for each app."""
        apps_base_dir = self._get_apps_base_dir()
        for app_name in self.app_names:
            self._create_app_file(apps_base_dir, app_name, "routes.j2", "routes.py")
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
