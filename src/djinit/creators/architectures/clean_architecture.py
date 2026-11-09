from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class CleanArchitectureHandler(ArchitectureHandler):
    @classmethod
    def scaffold_project(cls, file_creator: FileCreator) -> None:
        root = file_creator.project_root
        module_name = file_creator.module_name or "config"
        config_dir = os.path.join(root, module_name)
        settings_dir = os.path.join(config_dir, "settings")

        CommonUtils.create_directory_with_init(config_dir, f"Created {module_name}/__init__.py")
        CommonUtils.create_directory_with_init(settings_dir, f"Created {module_name}/settings/__init__.py")

        base_ctx = {
            "project_name": module_name,
            "app_names": [],
            "use_database_url": file_creator.metadata.get("use_database_url", False),
            "database_type": file_creator.metadata.get("database_type", "sqlite3"),
            "use_tailwind": False,
            "use_htmx": False,
            "use_vite": False,
        }
        file_creator._create_settings_package(settings_dir, base_ctx, module_name)
        file_creator._create_lifecycle_files(config_dir, module_name, api_module=None)

        apps_dir = os.path.join(root, "apps")
        CommonUtils.create_directory_with_init(apps_dir, "Created apps/__init__.py")

        initial_apps = file_creator.app_names or ["users", "core"]
        for app in initial_apps:
            cls.scaffold_app(app, apps_dir)

    @classmethod
    def scaffold_app(cls, app_name: str, apps_dir: str) -> bool:
        app_dir = os.path.join(apps_dir, app_name)
        os.makedirs(app_dir, exist_ok=True)
        CommonUtils.create_init_file(app_dir, f"Created {app_name}/__init__.py")

        pascal = app_name.title().replace("_", "")

        apps_py = f"""from django.apps import AppConfig


class {pascal}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{app_name}"
    verbose_name = "{pascal} Clean Architecture"
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "apps.py"), apps_py, f"Created {app_name}/apps.py")

        # 1. Domain
        domain_dir = os.path.join(app_dir, "domain")
        CommonUtils.create_directory_with_init(domain_dir, f"Created {app_name}/domain/__init__.py")
        domain_entities = f"""from dataclasses import dataclass


@dataclass
class {pascal}:
    id: int | None
    name: str
"""
        CommonUtils.create_file_with_content(
            os.path.join(domain_dir, "entities.py"), domain_entities, f"Created {app_name}/domain/entities.py"
        )

        # 2. Use Cases
        usecases_dir = os.path.join(app_dir, "use_cases")
        CommonUtils.create_directory_with_init(usecases_dir, f"Created {app_name}/use_cases/__init__.py")
        interactor_code = f"""from ..domain.entities import {pascal}


class Get{pascal}Interactor:
    def __init__(self, gateway):
        self.gateway = gateway

    def execute(self, pk: int) -> {pascal} | None:
        return self.gateway.get_by_id(pk)
"""
        CommonUtils.create_file_with_content(
            os.path.join(usecases_dir, "interactors.py"),
            interactor_code,
            f"Created {app_name}/use_cases/interactors.py",
        )

        # 3. Interfaces (Controllers & Gateways)
        interfaces_dir = os.path.join(app_dir, "interfaces")
        CommonUtils.create_directory_with_init(interfaces_dir, f"Created {app_name}/interfaces/__init__.py")
        controllers_code = f"""from django.http import JsonResponse
from ..infrastructure.adapters import Django{pascal}Gateway
from ..use_cases.interactors import Get{pascal}Interactor


def get_detail_view(request, pk: int):
    interactor = Get{pascal}Interactor(Django{pascal}Gateway())
    entity = interactor.execute(pk)
    if not entity:
        return JsonResponse({{"error": "Not found"}}, status=404)
    return JsonResponse({{"id": entity.id, "name": entity.name}})
"""
        CommonUtils.create_file_with_content(
            os.path.join(interfaces_dir, "controllers.py"),
            controllers_code,
            f"Created {app_name}/interfaces/controllers.py",
        )

        # 4. Infrastructure (Django DB Adapter & Models)
        infra_dir = os.path.join(app_dir, "infrastructure")
        CommonUtils.create_directory_with_init(infra_dir, f"Created {app_name}/infrastructure/__init__.py")

        models_code = f"""from django.db import models


class {pascal}Record(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "{app_name}_records"
"""
        CommonUtils.create_file_with_content(
            os.path.join(infra_dir, "models.py"), models_code, f"Created {app_name}/infrastructure/models.py"
        )

        adapters_code = f"""from ..domain.entities import {pascal}
from .models import {pascal}Record


class Django{pascal}Gateway:
    def get_by_id(self, pk: int) -> {pascal} | None:
        try:
            record = {pascal}Record.objects.get(pk=pk)
            return {pascal}(id=record.pk, name=record.name)
        except {pascal}Record.DoesNotExist:
            return None
"""
        CommonUtils.create_file_with_content(
            os.path.join(infra_dir, "adapters.py"), adapters_code, f"Created {app_name}/infrastructure/adapters.py"
        )

        # Root models.py for Django discovery
        models_root = f"""from .infrastructure.models import {pascal}Record

__all__ = ["{pascal}Record"]
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models.py"), models_root, f"Created {app_name}/models.py"
        )

        # URLs
        urls_code = f"""from django.urls import path
from .interfaces.controllers import get_detail_view

app_name = "{app_name}"

urlpatterns = [
    path("<int:pk>/", get_detail_view, name="detail"),
]
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "urls.py"), urls_code, f"Created {app_name}/urls.py")

        # Migrations & Admin & Tests
        migrations_dir = os.path.join(app_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        admin_py = f"""from django.contrib import admin
from .infrastructure.models import {pascal}Record

admin.site.register({pascal}Record)
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"), admin_py, f"Created {app_name}/admin.py"
        )

        tests_dir = os.path.join(app_dir, "tests")
        CommonUtils.create_directory_with_init(tests_dir, f"Created {app_name}/tests/__init__.py")

        test_code = f"""import pytest
from apps.{app_name}.infrastructure.models import {pascal}Record
from apps.{app_name}.infrastructure.adapters import Django{pascal}Gateway
from apps.{app_name}.use_cases.interactors import Get{pascal}Interactor


@pytest.mark.django_db
def test_clean_architecture_interactor():
    record = {pascal}Record.objects.create(name="Clean Item")
    interactor = Get{pascal}Interactor(Django{pascal}Gateway())
    entity = interactor.execute(record.pk)
    assert entity is not None
    assert entity.id == record.pk
    assert entity.name == "Clean Item"
"""
        CommonUtils.create_file_with_content(
            os.path.join(tests_dir, f"test_{app_name}.py"), test_code, f"Created {app_name}/tests/test_{app_name}.py"
        )

        return True


# ============================================================================
# 7. Multi-Tenant Architecture
# ============================================================================
