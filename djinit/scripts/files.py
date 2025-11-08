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
    create_init_file,
)


class FileManager:
    def __init__(self, project_root: str, project_name: str, app_names: list, metadata: dict):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
        # Use module name (e.g., 'config') for Django package paths if provided
        # Fall back to project_name if key present but None
        self.module_name = metadata.get("project_module_name") or project_name
        self.project_configs = os.path.join(project_root, self.module_name)
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
            context = {
                "project_name": self.project_name,
                "app_names": self.app_names,
                "predefined_structure": bool(self.metadata.get("predefined_structure")),
                "module_name": self.module_name,
            }
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
            # Default package_name to "backend" if it's "." or empty
            package_name = metadata.get("package_name", "backend")
            if package_name == "." or not package_name:
                package_name = "backend"
            context = {"package_name": package_name, "project_name": self.project_name}
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

    def create_predefined_structure(self) -> bool:
        """Create the predefined project structure under apps/ and api/ using custom templates.

        Expected layout:
        - apps/users with nested folders (models, serializers, services, views, tests)
        - apps/core with utils, mixins, exceptions, middleware
        - api/ with versioned urls
        - overwrite project urls to include api urls
        """
        # Ensure apps package
        apps_dir = os.path.join(self.project_root, "apps")
        os.makedirs(apps_dir, exist_ok=True)
        create_init_file(apps_dir, "Created apps/__init__.py")

        # users app
        users_dir = os.path.join(apps_dir, "users")
        os.makedirs(users_dir, exist_ok=True)
        create_init_file(users_dir, "Created apps/users/__init__.py")

        # apps.py can reuse standard app template
        users_context = {"app_name": "users"}
        users_apps_py = template_engine.render_template("app/apps.j2", users_context)
        create_file_with_content(os.path.join(users_dir, "apps.py"), users_apps_py, "Created apps/users/apps.py")

        # Nested folders and files for users
        users_subfolders = {
            "models": [
                ("user.py", "custom/users/models_user.j2"),
            ],
            "serializers": [
                ("user_serializer.py", "custom/users/serializers_user.j2"),
            ],
            "services": [
                ("user_service.py", "custom/users/services_user.j2"),
            ],
            "views": [
                ("user_view.py", "custom/users/views_user.j2"),
            ],
            "tests": [
                ("test_user_api.py", "custom/users/tests_user_api.j2"),
            ],
        }
        for folder, files in users_subfolders.items():
            folder_path = os.path.join(users_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            create_init_file(folder_path, f"Created apps/users/{folder}/__init__.py")
            for filename, tpl in files:
                content = template_engine.render_template(tpl, {"app_module": "apps.users"})
                create_file_with_content(
                    os.path.join(folder_path, filename),
                    content,
                    f"Created apps/users/{folder}/{filename}",
                )

        # users urls.py at app root
        users_urls_content = template_engine.render_template("custom/users/urls.j2", {"app_module": "apps.users"})
        create_file_with_content(os.path.join(users_dir, "urls.py"), users_urls_content, "Created apps/users/urls.py")

        # core app
        core_dir = os.path.join(apps_dir, "core")
        os.makedirs(core_dir, exist_ok=True)
        create_init_file(core_dir, "Created apps/core/__init__.py")

        # core subfolders and files
        core_subfolders = {
            "utils": [("responses.py", "custom/core/utils_responses.j2")],
            "mixins": [("timestamped_model.py", "custom/core/mixins_timestamped_model.j2")],
            "middleware": [("request_logger.py", "custom/core/middleware_request_logger.j2")],
        }
        for folder, files in core_subfolders.items():
            folder_path = os.path.join(core_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            create_init_file(folder_path, f"Created apps/core/{folder}/__init__.py")
            for filename, tpl in files:
                content = template_engine.render_template(tpl, {})
                create_file_with_content(
                    os.path.join(folder_path, filename),
                    content,
                    f"Created apps/core/{folder}/{filename}",
                )

        # core/exceptions.py
        exceptions_content = template_engine.render_template("custom/core/exceptions.j2", {})
        create_file_with_content(os.path.join(core_dir, "exceptions.py"), exceptions_content, "Created apps/core/exceptions.py")

        # api package
        api_dir = os.path.join(self.project_root, "api")
        os.makedirs(api_dir, exist_ok=True)
        create_init_file(api_dir, "Created api/__init__.py")
        api_urls_content = template_engine.render_template("custom/api/urls.j2", {})
        create_file_with_content(os.path.join(api_dir, "urls.py"), api_urls_content, "Created api/urls.py")

        # api/v1
        api_v1_dir = os.path.join(api_dir, "v1")
        os.makedirs(api_v1_dir, exist_ok=True)
        create_init_file(api_v1_dir, "Created api/v1/__init__.py")
        api_v1_urls_content = template_engine.render_template("custom/api/v1_urls.j2", {})
        create_file_with_content(os.path.join(api_v1_dir, "urls.py"), api_v1_urls_content, "Created api/v1/urls.py")

        # overwrite project urls to include api
        project_urls_content = template_engine.render_template("custom/project_urls_api.j2", {"project_module": self.module_name})
        create_file_with_content(
            os.path.join(self.project_configs, "urls.py"),
            project_urls_content,
            "Updated project urls.py to include API routes",
            should_format=True,
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

            context = {"project_name": self.project_name, "module_name": self.module_name}
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
            context = {"project_name": self.project_name, "module_name": self.module_name}
            gitlab_ci_content = template_engine.render_template("shared/gitlab_ci.j2", context)
            create_file_with_content(
                ".gitlab-ci.yml",
                gitlab_ci_content,
                "Created GitLab CI configuration (.gitlab-ci.yml)",
            )
        return True
