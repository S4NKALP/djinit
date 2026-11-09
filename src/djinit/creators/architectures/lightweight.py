from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils
from djinit.utils.django import DjangoHelper

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class LightweightHandler(ArchitectureHandler):
    @classmethod
    def scaffold_project(cls, file_creator: FileCreator) -> None:
        root = file_creator.project_root
        module_name = file_creator.module_name or file_creator.project_name
        project_dir = os.path.join(root, module_name)
        settings_dir = os.path.join(project_dir, "settings")

        CommonUtils.create_directory_with_init(project_dir, f"Created {module_name}/__init__.py")
        CommonUtils.create_directory_with_init(settings_dir, f"Created {module_name}/settings/__init__.py")

        base_ctx = {
            "project_name": module_name,
            "app_names": [],
            "use_database_url": False,
            "database_type": "sqlite3",
            "use_tailwind": False,
            "use_htmx": False,
            "use_vite": False,
        }
        file_creator._create_settings_package(settings_dir, base_ctx, module_name)
        file_creator._create_lifecycle_files(project_dir, module_name, api_module=None)

        # Minimal static & template dirs
        os.makedirs(os.path.join(root, "static"), exist_ok=True)
        templates_dir = os.path.join(root, "templates")
        os.makedirs(templates_dir, exist_ok=True)

        home_html = """<!DOCTYPE html>
<html>
<head>
    <title>Welcome to Django</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
        h1 { color: #092e20; }
    </style>
</head>
<body>
    <h1>It works!</h1>
    <p>Your lightweight Django application is running smoothly.</p>
</body>
</html>
"""
        CommonUtils.create_file_with_content(
            os.path.join(templates_dir, "home.html"), home_html, "Created templates/home.html"
        )

        # Initial app if requested
        if file_creator.app_names:
            for app in file_creator.app_names:
                cls.scaffold_app(app, root)

    @classmethod
    def scaffold_app(cls, app_name: str, apps_dir: str) -> bool:
        # Standard lightweight django startapp
        return DjangoHelper.startapp(app_name, apps_dir, app_name)


# ============================================================================
# 5. Domain-Driven Design (DDD)
# ============================================================================
