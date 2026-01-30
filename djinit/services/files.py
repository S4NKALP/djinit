"""
File management utilities for djinit.
Handles creation and modification of project files.
"""

import os

from djinit.services.templates import template_engine
from djinit.utils.common import (
    calculate_app_module_paths,
    change_cwd,
    create_directory_with_init,
    create_file_from_template,
    create_file_with_content,
    get_package_name,
)


class FileManager:
    def __init__(self, project_root: str, project_name: str, app_names: list, metadata: dict):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.metadata = metadata
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
    ) -> None:
        """Helper to render template and create file."""
        target_dir = base_dir or self.project_root
        with change_cwd(target_dir):
            content = template_engine.render_template(template_path, context)
            create_file_with_content(filepath, content, message, should_format=should_format)

    def _create_files_from_specs(self, base_dir: str, folder_specs: dict, base_context: dict = None) -> None:
        """Helper to create multiple folders and files from a specification dict."""
        base_context = base_context or {}

        for folder_name, file_templates in folder_specs.items():
            folder_path = os.path.join(base_dir, folder_name)
            create_directory_with_init(folder_path, f"Created {folder_path}/__init__.py")

            for filename, template_path in file_templates:
                file_path = os.path.join(folder_path, filename)
                create_file_from_template(file_path, template_path, base_context, f"Created {file_path}")

    def _create_apps_py(self, app_dir: str, app_name: str, message: str = None, should_format: bool = False) -> None:
        """Helper to create apps.py file for an app."""
        apps_py_path = os.path.join(app_dir, "apps.py")
        context = {"app_name": app_name} if app_name else {}
        msg = message or f"Created {os.path.basename(app_dir)}/apps.py"
        create_file_from_template(apps_py_path, "components/apps.py-tpl", context, msg, should_format=should_format)

    def _create_subdirectories_with_init(self, base_dir: str, subdirs: list, prefix: str = "") -> None:
        """Helper to create multiple subdirectories with __init__.py files."""
        for subdir in subdirs:
            subdir_path = os.path.join(base_dir, subdir)
            message = f"Created {prefix}{subdir}/__init__.py" if prefix else f"Created {subdir}/__init__.py"
            create_directory_with_init(subdir_path, message)

    def _create_settings_package(self, settings_dir: str, base_context: dict, prefix: str) -> None:
        """Helper to create settings package files (base, development, production)."""
        from djinit.utils.secretkey import generate_secret_key

        secret_key = generate_secret_key()
        dev_context = {"secret_key": secret_key}

        # Prepare context for base.py with full AppConfig paths
        base_settings_context = base_context.copy()
        if "app_names" in base_settings_context:
            transformed_apps = []
            for app in base_settings_context["app_names"]:
                # Transform to full AppConfig path: module.path -> module.path.apps.ConfigName
                short_name = app.split('.')[-1]
                config_name = short_name.title().replace('_', '') + 'Config'
                # If it's the special "apps" container in unified structure, we might want to skip or handle differently
                # But assumes all user apps follow standard djinit structure
                full_path = f"{app}.apps.{config_name}"
                transformed_apps.append(full_path)
            base_settings_context["app_names"] = transformed_apps

        for filename, context in [
            ("base.py", base_settings_context),
            ("development.py", dev_context),
            ("production.py", base_settings_context),
        ]:
            filepath = os.path.join(settings_dir, filename)
            template_path = f"config/settings/{filename.replace('.py', '')}.py-tpl"
            self._render_and_create_file(
                filepath,
                template_path,
                context,
                f"Created {prefix}/settings/{filename}",
                base_dir=os.path.dirname(
                    settings_dir
                ),  # Not strictly used by _render_and_create_file but good for context
                should_format=True,
            )

    def _create_lifecycle_files(
        self, target_dir: str, prefix: str, api_module: str = None, comment_out_api: bool = False
    ) -> None:
        """Helper to create urls.py, wsgi.py, and asgi.py."""

        urls_context = {"url_type": "project", "api_module": api_module, "include_api": True}
        if comment_out_api:
            urls_context["comment_out_api_url"] = True

        files = [
            ("urls.py", "config/urls.py-tpl", urls_context),
            ("wsgi.py", "config/wsgi.py-tpl", {"project_name": prefix}),
            ("asgi.py", "config/asgi.py-tpl", {"project_name": prefix}),
        ]

        for filename, template, context in files:
            filepath = os.path.join(target_dir, filename)
            self._render_and_create_file(
                filepath, template, context, f"Created {prefix}/{filename}", should_format=True
            )

    def create_gitignore(self) -> None:
        self._render_and_create_file(".gitignore", "project/gitignore-tpl", {}, "Created .gitignore file")

    def create_requirements(self) -> None:
        context = {
            "use_database_url": self.metadata.get("use_database_url", True),
            "database_type": self.metadata.get("database_type", "postgresql"),
        }
        self._render_and_create_file(
            "requirements.txt",
            "project/requirements-tpl",
            context,
            "Created requirements.txt with Django dependencies",
        )

    def create_readme(self) -> None:
        context = {
            "project_name": self.project_name,
            "app_names": self.app_names,
            "predefined_structure": bool(self.metadata.get("predefined_structure")),
            "unified_structure": bool(self.metadata.get("unified_structure")),
            "module_name": self.module_name,
        }
        self._render_and_create_file("README.md", "project/readme.md-tpl", context, "Created README.md file")

    def create_env_file(self) -> None:
        """Create .env.sample file with environment variables."""
        context = {
            "project_name": self.module_name,
            "use_database_url": self.metadata.get("use_database_url", True),
            "database_type": self.metadata.get("database_type", "postgresql"),
        }
        self._render_and_create_file(
            ".env.sample",
            "project/env_sample-tpl",
            context,
            "Created .env.sample file with generated secret key",
        )

    def create_pyproject(self, metadata: dict) -> None:
        package_name = metadata.get("package_name", "backend")
        package_name = get_package_name(package_name)
        context = {
            "package_name": package_name,
            "project_name": self.project_name,
            "database_type": metadata.get("database_type", "postgresql"),
        }
        self._render_and_create_file(
            "pyproject.toml",
            "project/pyproject.toml-tpl",
            context,
            "Created pyproject.toml file for uv",
        )

    def create_project_urls(self) -> None:
        """Create project urls.py using project_config/urls.py-tpl template (replaces update_project_urls)."""
        effective_app_modules = calculate_app_module_paths(self.app_names, self.metadata)
        context = {
            "url_type": "project",
            "project_name": self.project_name,
            "app_names": effective_app_modules,
            "include_apps": True,
            "include_api": True,
        }
        self._render_and_create_file(
            "urls.py",
            "config/urls.py-tpl",
            context,
            "Created project urls.py with comprehensive URL configuration",
            base_dir=self.project_configs,
            should_format=True,
        )

    def create_justfile(self) -> None:
        context = {"project_name": self.project_name}
        self._render_and_create_file(
            "justfile",
            "project/justfile-tpl",
            context,
            "Created justfile with Django development tasks",
        )

    def create_predefined_structure(self) -> None:
        apps_dir = os.path.join(self.project_root, "apps")
        create_directory_with_init(apps_dir, "Created apps/__init__.py")

        users_dir = os.path.join(apps_dir, "users")
        create_directory_with_init(users_dir, "Created apps/users/__init__.py")
        self._create_apps_py(users_dir, "users")

        users_subfolders = {
            "models": [("user.py", "presets/predefined/apps/users/models.py-tpl")],
            "serializers": [("user_serializer.py", "presets/predefined/apps/users/serializers.py-tpl")],
            "services": [("user_service.py", "presets/predefined/apps/users/services.py-tpl")],
            "views": [("user_view.py", "presets/predefined/apps/users/views.py-tpl")],
            "tests": [("test_user_api.py", "presets/predefined/apps/users/tests.py-tpl")],
        }
        self._create_files_from_specs(users_dir, users_subfolders, {"app_module": "apps.users"})

        users_urls_path = os.path.join(users_dir, "urls.py")
        create_file_from_template(
            users_urls_path,
            "config/urls.py-tpl",
            {"url_type": "drf_router", "app_module": "apps.users", "view_file": "user_view", "viewset_name": "UserViewSet", "router_prefix": "users", "basename": "users", "has_viewset": True, "has_app_name": True, "app_name": "users", "has_include": True},
            "Created apps/users/urls.py",
        )

        core_dir = os.path.join(apps_dir, "core")
        create_directory_with_init(core_dir, "Created apps/core/__init__.py")

        core_subfolders = {
            "utils": [("responses.py", "presets/predefined/core/utils/responses.py-tpl")],
            "mixins": [("timestamped_model.py", "presets/predefined/core/mixins/timestamped_model.py-tpl")],
            "middleware": [("request_logger.py", "presets/predefined/core/middleware/request_logger.py-tpl")],
        }
        self._create_files_from_specs(core_dir, core_subfolders, {})

        exceptions_path = os.path.join(core_dir, "exceptions.py")
        create_file_from_template(
            exceptions_path, "presets/predefined/core/exceptions.py-tpl", {}, "Created apps/core/exceptions.py"
        )

        api_dir = os.path.join(self.project_root, "api")
        create_directory_with_init(api_dir, "Created api/__init__.py")
        api_urls_path = os.path.join(api_dir, "urls.py")
        create_file_from_template(api_urls_path, "config/urls.py-tpl", {"url_type": "api_root", "app_name": "api", "version": "v1", "api_module": "api"}, "Created api/urls.py")

        api_v1_dir = os.path.join(api_dir, "v1")
        create_directory_with_init(api_v1_dir, "Created api/v1/__init__.py")
        api_v1_urls_path = os.path.join(api_v1_dir, "urls.py")
        create_file_from_template(api_v1_urls_path, "config/urls.py-tpl", {"url_type": "api_version", "app_name": "v1", "app_list": ["users"], "app_module": "apps"}, "Created api/v1/urls.py")

        project_urls_path = os.path.join(self.project_configs, "urls.py")
        create_file_from_template(
            project_urls_path,
            "config/urls.py-tpl",
            {"url_type": "project", "api_module": "api", "include_api": True},
            "Updated project urls.py to include API routes",
            should_format=True,
        )

    def create_unified_structure(self) -> None:
        # 1. Create 'core' directory (Project Config)
        core_dir = os.path.join(self.project_root, "core")
        create_directory_with_init(core_dir, "Created core/__init__.py")

        settings_dir = os.path.join(core_dir, "settings")
        create_directory_with_init(settings_dir, "Created core/settings/__init__.py")

        # Create settings files
        base_context = {
            "project_name": "core",
            "app_names": ["apps"],
            "use_database_url": self.metadata.get("use_database_url", True),
            "database_type": self.metadata.get("database_type", "postgresql"),
        }
        self._create_settings_package(settings_dir, base_context, "core")

        # Create lifecycle files (urls, wsgi, asgi)
        self._create_lifecycle_files(core_dir, "core", api_module="apps.api")

        # 2. Create 'apps' directory (The Main App)
        apps_dir = os.path.join(self.project_root, "apps")
        create_directory_with_init(apps_dir, "Created apps/__init__.py")

        # Create apps.py for the 'apps' app
        self._create_apps_py(apps_dir, "apps", "Created apps/apps.py", should_format=True)

        # Create sub-components as directories with __init__.py
        components = ["admin", "models", "serializers", "tests", "urls", "views"]
        self._create_subdirectories_with_init(apps_dir, components, "apps/")

        # Create 'api' directory with v1
        api_dir = os.path.join(apps_dir, "api")
        create_directory_with_init(api_dir, "Created apps/api/__init__.py")

        create_file_from_template(
            os.path.join(api_dir, "urls.py"),
            "config/urls.py-tpl",
            {"url_type": "api_root", "app_name": "api", "version": "v1", "api_module": "apps.api"},
            "Created apps/api/urls.py",
            should_format=True,
        )

        api_v1_dir = os.path.join(api_dir, "v1")
        create_directory_with_init(api_v1_dir, "Created apps/api/v1/__init__.py")

        create_file_from_template(
            os.path.join(api_v1_dir, "urls.py"),
            "config/urls.py-tpl",
            {"url_type": "api_version", "app_name": "v1", "app_list": [], "app_module": "apps"},
            "Created apps/api/v1/urls.py",
            should_format=True,
        )

    def create_single_structure(self) -> None:
        project_dir = os.path.join(self.project_root, self.module_name)
        create_directory_with_init(project_dir, f"Created {self.module_name}/__init__.py")

        settings_dir = os.path.join(project_dir, "settings")
        create_directory_with_init(settings_dir, f"Created {self.module_name}/settings/__init__.py")

        # Create settings files
        base_context = {
            "project_name": self.module_name,
            "app_names": [self.module_name],
            "use_database_url": self.metadata.get("use_database_url", True),
            "database_type": self.metadata.get("database_type", "postgresql"),
        }
        self._create_settings_package(settings_dir, base_context, self.module_name)

        # Create lifecycle files (urls, wsgi, asgi)
        self._create_lifecycle_files(
            project_dir, self.module_name, api_module=f"{self.module_name}.api", comment_out_api=True
        )

        components = ["admin", "api", "models", "tests"]
        self._create_subdirectories_with_init(project_dir, components, f"{self.module_name}/")

        create_file_from_template(
            os.path.join(project_dir, "admin", "__init__.py"),
            "components/admin.py-tpl",
            {},
            f"Created {self.module_name}/admin/__init__.py",
        )

        create_file_from_template(
            os.path.join(project_dir, "models", "__init__.py"),
            "components/models.py-tpl",
            {},
            f"Created {self.module_name}/models/__init__.py",
        )

        create_file_from_template(
            os.path.join(project_dir, "api", "README.md"),
            "components/api_readme.md-tpl",
            {"module_name": self.module_name},
            f"Created {self.module_name}/api/README.md",
        )

        create_file_from_template(
            os.path.join(project_dir, "models", "README.md"),
            "components/models_readme.md-tpl",
            {"module_name": self.module_name},
            f"Created {self.module_name}/models/README.md",
        )

    def create_procfile(self) -> None:
        context = {"project_name": self.project_name}
        self._render_and_create_file(
            "Procfile",
            "project/procfile-tpl",
            context,
            "Created Procfile with Gunicorn configuration",
        )

    def create_runtime_txt(self) -> None:
        context = {"python_version": "3.13"}
        self._render_and_create_file(
            "runtime.txt",
            "project/runtime_txt-tpl",
            context,
            "Created runtime.txt with Python version specification",
        )

    def create_github_actions(self) -> None:
        github_dir = os.path.join(self.project_root, ".github", "workflows")
        os.makedirs(github_dir, exist_ok=True)
        context = {"project_name": self.project_name, "module_name": self.module_name}
        workflow_file = os.path.join(github_dir, "ci.yml")
        self._render_and_create_file(
            workflow_file,
            "project/ci/github_actions-tpl",
            context,
            "Created Github Actions workflow (ci.yml)",
            base_dir=self.project_root,
        )

    def create_gitlab_ci(self) -> None:
        context = {"project_name": self.project_name, "module_name": self.module_name}
        self._render_and_create_file(
            ".gitlab-ci.yml",
            "project/ci/gitlab_ci-tpl",
            context,
            "Created GitLab CI configuration (.gitlab-ci.yml)",
        )

    def create_djinit_config(self) -> None:
        """Create .djinit configuration file."""
        import json

        is_predefined = self.metadata.get("predefined_structure", False)
        is_unified = self.metadata.get("unified_structure", False)
        is_single = self.metadata.get("single_structure", False)
        is_standard = not (is_predefined or is_unified or is_single)

        config = {
            "project_name": self.project_name,
            "structure": {
                "standard": is_standard,
                "predefined": is_predefined,
                "unified": is_unified,
                "single": is_single,
            },
            "apps": {
                "nested": self.metadata.get("nested_apps", False),
                "nested_dir": self.metadata.get("nested_dir"),
            },
            "settings": {
                "use_database_url": self.metadata.get("use_database_url", True),
                "database_type": self.metadata.get("database_type", "postgresql"),
            },
            "cicd": {
                "github": self.metadata.get("use_github_actions", False),
                "gitlab": self.metadata.get("use_gitlab_ci", False),
            },
        }

        filepath = os.path.join(self.project_root, ".djinit")
        create_file_with_content(filepath, json.dumps(config, indent=4), "Created .djinit configuration file")
