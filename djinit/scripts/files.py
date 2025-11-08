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

    def _render_and_create_file(
        self,
        filepath: str,
        template_path: str,
        context: dict,
        message: str,
        base_dir: str = None,
        should_format: bool = False,
    ) -> bool:
        """Helper to render template and create file."""
        target_dir = base_dir or self.project_root
        with change_cwd(target_dir):
            content = template_engine.render_template(template_path, context)
            return create_file_with_content(filepath, content, message, should_format=should_format)

    def _ensure_directory_with_init(self, dir_path: str, message: str) -> None:
        """Helper to create directory and __init__.py file."""
        os.makedirs(dir_path, exist_ok=True)
        create_init_file(dir_path, message)

    def _create_files_from_specs(self, base_dir: str, folder_specs: dict, base_context: dict = None) -> None:
        """Helper to create multiple folders and files from a specification dict."""
        base_context = base_context or {}
        for folder, files in folder_specs.items():
            folder_path = os.path.join(base_dir, folder)
            self._ensure_directory_with_init(folder_path, f"Created {folder_path}/__init__.py")
            for filename, template_path in files:
                file_path = os.path.join(folder_path, filename)
                content = template_engine.render_template(template_path, base_context)
                create_file_with_content(file_path, content, f"Created {file_path}")

    def create_gitignore(self) -> bool:
        return self._render_and_create_file(".gitignore", "shared/gitignore.j2", {}, "Created .gitignore file")

    def create_requirements(self) -> bool:
        context = {"use_database_url": self.metadata.get("use_database_url", True)}
        return self._render_and_create_file(
            "requirements.txt",
            "shared/requirements.j2",
            context,
            "Created requirements.txt with Django dependencies",
        )

    def create_readme(self) -> bool:
        context = {
            "project_name": self.project_name,
            "app_names": self.app_names,
            "predefined_structure": bool(self.metadata.get("predefined_structure")),
            "unified_structure": bool(self.metadata.get("unified_structure")),
            "module_name": self.module_name,
        }
        return self._render_and_create_file("README.md", "shared/readme.j2", context, "Created README.md file")

    def create_env_file(self) -> bool:
        """Create .env.sample file with environment variables."""
        context = {
            "project_name": self.project_name,
            "use_database_url": self.metadata.get("use_database_url", True),
        }
        return self._render_and_create_file(
            ".env.sample",
            "shared/env_sample.j2",
            context,
            "Created .env.sample file with generated secret key",
        )

    def create_pyproject_toml(self, metadata: dict) -> bool:
        # Default package_name to "backend" if it's "." or empty
        package_name = metadata.get("package_name", "backend")
        if package_name == "." or not package_name:
            package_name = "backend"
        context = {"package_name": package_name, "project_name": self.project_name}
        return self._render_and_create_file(
            "pyproject.toml",
            "shared/pyproject_toml.j2",
            context,
            "Created pyproject.toml file for uv",
        )

    def create_project_urls(self) -> bool:
        """Create project urls.py using project_urls.j2 template (replaces update_project_urls)."""
        effective_app_modules = calculate_app_module_paths(self.app_names, self.metadata)
        context = {
            "project_name": self.project_name,
            "app_names": effective_app_modules,
        }
        return self._render_and_create_file(
            "urls.py",
            "project/urls_with_apps.j2",
            context,
            "Created project urls.py with comprehensive URL configuration",
            base_dir=self.project_configs,
            should_format=True,
        )

    def create_justfile(self) -> bool:
        context = {"project_name": self.project_name}
        return self._render_and_create_file(
            "justfile",
            "shared/justfile.j2",
            context,
            "Created justfile with Django development tasks",
        )

    def create_predefined_structure(self) -> bool:
        # Ensure apps package
        apps_dir = os.path.join(self.project_root, "apps")
        self._ensure_directory_with_init(apps_dir, "Created apps/__init__.py")

        # users app
        users_dir = os.path.join(apps_dir, "users")
        self._ensure_directory_with_init(users_dir, "Created apps/users/__init__.py")

        # apps.py can reuse standard app template
        users_apps_path = os.path.join(users_dir, "apps.py")
        content = template_engine.render_template("base/apps.j2", {"app_name": "users"})
        create_file_with_content(users_apps_path, content, "Created apps/users/apps.py")

        # Nested folders and files for users
        users_subfolders = {
            "models": [("user.py", "predefined/apps/users/models.j2")],
            "serializers": [("user_serializer.py", "predefined/apps/users/serializers.j2")],
            "services": [("user_service.py", "predefined/apps/users/services.j2")],
            "views": [("user_view.py", "predefined/apps/users/views.j2")],
            "tests": [("test_user_api.py", "predefined/apps/users/tests.j2")],
        }
        self._create_files_from_specs(users_dir, users_subfolders, {"app_module": "apps.users"})

        # users urls.py at app root
        users_urls_path = os.path.join(users_dir, "urls.py")
        content = template_engine.render_template("predefined/apps/users/urls.j2", {"app_module": "apps.users"})
        create_file_with_content(users_urls_path, content, "Created apps/users/urls.py")

        # core app
        core_dir = os.path.join(apps_dir, "core")
        self._ensure_directory_with_init(core_dir, "Created apps/core/__init__.py")

        # core subfolders and files
        core_subfolders = {
            "utils": [("responses.py", "predefined/core/utils/responses.j2")],
            "mixins": [("timestamped_model.py", "predefined/core/mixins/timestamped_model.j2")],
            "middleware": [("request_logger.py", "predefined/core/middleware/request_logger.j2")],
        }
        self._create_files_from_specs(core_dir, core_subfolders, {})

        # core/exceptions.py
        exceptions_path = os.path.join(core_dir, "exceptions.py")
        content = template_engine.render_template("predefined/core/exceptions.j2", {})
        create_file_with_content(exceptions_path, content, "Created apps/core/exceptions.py")

        # api package
        api_dir = os.path.join(self.project_root, "api")
        self._ensure_directory_with_init(api_dir, "Created api/__init__.py")
        api_urls_path = os.path.join(api_dir, "urls.py")
        content = template_engine.render_template("predefined/api/urls.j2", {})
        create_file_with_content(api_urls_path, content, "Created api/urls.py")

        # api/v1
        api_v1_dir = os.path.join(api_dir, "v1")
        self._ensure_directory_with_init(api_v1_dir, "Created api/v1/__init__.py")
        api_v1_urls_path = os.path.join(api_v1_dir, "urls.py")
        content = template_engine.render_template("predefined/api/v1/urls.j2", {})
        create_file_with_content(api_v1_urls_path, content, "Created api/v1/urls.py")

        # overwrite project urls to include api
        project_urls_path = os.path.join(self.project_configs, "urls.py")
        content = template_engine.render_template("project/urls_with_api.j2", {"api_module": "api"})
        create_file_with_content(
            project_urls_path, content, "Updated project urls.py to include API routes", should_format=True
        )

        return True

    def create_unified_structure(self) -> bool:
        # Create core directory structure
        core_dir = os.path.join(self.project_root, "core")
        self._ensure_directory_with_init(core_dir, "Created core/__init__.py")

        # Create core/settings directory
        settings_dir = os.path.join(core_dir, "settings")
        self._ensure_directory_with_init(settings_dir, "Created core/settings/__init__.py")

        # Generate secret key for development settings
        from djinit.scripts.secretkey_generator import generate_secret_key

        secret_key = generate_secret_key()

        # Create settings files using project templates with unified context
        # For unified structure, project_module_name is "core"
        base_context = {
            "project_name": "core",  # Use "core" as the module name
            "app_names": ["apps.core", "apps.api"] + [f"apps.{app}" for app in self.app_names],
            "use_database_url": self.metadata.get("use_database_url", True),
        }
        dev_context = {"secret_key": secret_key}

        # Settings files
        for filename, context in [
            ("base.py", base_context),
            ("development.py", dev_context),
            ("production.py", base_context),
        ]:
            filepath = os.path.join(settings_dir, filename)
            content = template_engine.render_template(f"project/settings/{filename.replace('.py', '')}.j2", context)
            create_file_with_content(filepath, content, f"Created core/settings/{filename}", should_format=True)

        # Core project files
        core_files = [
            ("urls.py", "project/urls_with_api.j2", {"api_module": "apps.api"}),
            ("wsgi.py", "project/wsgi.j2", {}),
            ("asgi.py", "project/asgi.j2", {}),
        ]
        for filename, template, context in core_files:
            filepath = os.path.join(core_dir, filename)
            content = template_engine.render_template(template, context)
            create_file_with_content(filepath, content, f"Created core/{filename}", should_format=True)

        # Create apps directory
        apps_dir = os.path.join(self.project_root, "apps")
        self._ensure_directory_with_init(apps_dir, "Created apps/__init__.py")

        # Create apps/core
        apps_core_dir = os.path.join(apps_dir, "core")
        self._ensure_directory_with_init(apps_core_dir, "Created apps/core/__init__.py")

        # Create apps/core/apps.py
        apps_py_path = os.path.join(apps_core_dir, "apps.py")
        content = template_engine.render_template("base/apps.j2", {})
        create_file_with_content(apps_py_path, content, "Created apps/core/apps.py", should_format=True)

        # Create apps/core/models
        models_dir = os.path.join(apps_core_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        model_files = [
            ("__init__.py", "base/models.j2"),
            ("base.py", "unified/apps/core/models/base.py.j2"),
            ("mixins.py", "unified/apps/core/models/mixins.py.j2"),
        ]
        for filename, template in model_files:
            filepath = os.path.join(models_dir, filename)
            content = template_engine.render_template(template, {})
            create_file_with_content(filepath, content, f"Created apps/core/models/{filename}", should_format=True)

        # Create apps/core/utils
        utils_dir = os.path.join(apps_core_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        utils_files = [
            ("__init__.py", "unified/apps/core/utils/__init__.py.j2"),
            ("responses.py", "unified/apps/core/utils/responses.py.j2"),
        ]
        for filename, template in utils_files:
            filepath = os.path.join(utils_dir, filename)
            content = template_engine.render_template(template, {})
            create_file_with_content(filepath, content, f"Created apps/core/utils/{filename}", should_format=True)

        # Create apps/core/permissions and middleware
        for subdir in ["permissions", "middleware"]:
            subdir_path = os.path.join(apps_core_dir, subdir)
            self._ensure_directory_with_init(subdir_path, f"Created apps/core/{subdir}/__init__.py")

        # Create apps/api
        apps_api_dir = os.path.join(apps_dir, "api")
        self._ensure_directory_with_init(apps_api_dir, "Created apps/api/__init__.py")

        # Create apps/api/apps.py
        apps_py_path = os.path.join(apps_api_dir, "apps.py")
        content = template_engine.render_template("base/apps.j2", {"app_name": "apps.api"})
        create_file_with_content(apps_py_path, content, "Created apps/api/apps.py", should_format=True)

        # Create apps/api subdirectories
        api_subdirs = ["models", "serializers", "views", "services", "tests", "urls", "admin"]
        for subdir in api_subdirs:
            subdir_path = os.path.join(apps_api_dir, subdir)
            self._ensure_directory_with_init(subdir_path, f"Created apps/api/{subdir}/__init__.py")

        return True

    def create_procfile(self) -> bool:
        context = {"project_name": self.project_name}
        return self._render_and_create_file(
            "Procfile",
            "shared/procfile.j2",
            context,
            "Created Procfile with Gunicorn configuration",
        )

    def create_runtime_txt(self) -> bool:
        context = {"python_version": "3.13"}
        return self._render_and_create_file(
            "runtime.txt",
            "shared/runtime_txt.j2",
            context,
            "Created runtime.txt with Python version specification",
        )

    def create_github_actions(self) -> bool:
        github_dir = os.path.join(self.project_root, ".github", "workflows")
        os.makedirs(github_dir, exist_ok=True)
        context = {"project_name": self.project_name, "module_name": self.module_name}
        workflow_file = os.path.join(github_dir, "ci.yml")
        return self._render_and_create_file(
            workflow_file,
            "shared/ci/github_actions.j2",
            context,
            "Created Github Actions workflow (ci.yml)",
            base_dir=self.project_root,
        )

    def create_gitlab_ci(self) -> bool:
        context = {"project_name": self.project_name, "module_name": self.module_name}
        return self._render_and_create_file(
            ".gitlab-ci.yml",
            "shared/ci/gitlab_ci.j2",
            context,
            "Created GitLab CI configuration (.gitlab-ci.yml)",
        )
