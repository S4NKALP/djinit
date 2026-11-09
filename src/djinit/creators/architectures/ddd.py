from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class DDDHandler(ArchitectureHandler):
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

        initial_apps = file_creator.app_names or ["orders", "core"]
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
    verbose_name = "{pascal} Domain"
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "apps.py"), apps_py, f"Created {app_name}/apps.py")

        # Layer 1: Domain
        domain_dir = os.path.join(app_dir, "domain")
        CommonUtils.create_directory_with_init(domain_dir, f"Created {app_name}/domain/__init__.py")

        entities_py = f"""from dataclasses import dataclass
from datetime import datetime


@dataclass
class {pascal}Entity:
    id: int | None
    code: str
    status: str
    created_at: datetime | None = None

    def can_transition_to(self, new_status: str) -> bool:
        valid_transitions = {{"draft": ["submitted"], "submitted": ["approved", "rejected"]}}
        return new_status in valid_transitions.get(self.status, [])
"""
        CommonUtils.create_file_with_content(
            os.path.join(domain_dir, "entities.py"), entities_py, f"Created {app_name}/domain/entities.py"
        )

        # Layer 2: Application
        app_layer_dir = os.path.join(app_dir, "application")
        CommonUtils.create_directory_with_init(app_layer_dir, f"Created {app_name}/application/__init__.py")

        use_cases_py = f"""from dataclasses import dataclass
from ..domain.entities import {pascal}Entity
from ..infrastructure.repositories import Django{pascal}Repository


@dataclass
class Create{pascal}Command:
    code: str


class Create{pascal}UseCase:
    def __init__(self, repository: Django{pascal}Repository | None = None):
        self.repository = repository or Django{pascal}Repository()

    def execute(self, command: Create{pascal}Command) -> {pascal}Entity:
        entity = {pascal}Entity(id=None, code=command.code, status="draft")
        return self.repository.save(entity)
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_layer_dir, "use_cases.py"), use_cases_py, f"Created {app_name}/application/use_cases.py"
        )

        # Layer 3: Infrastructure (Persistence Models & Adapters)
        infra_dir = os.path.join(app_dir, "infrastructure")
        CommonUtils.create_directory_with_init(infra_dir, f"Created {app_name}/infrastructure/__init__.py")

        models_py = f"""from django.db import models


class {pascal}Model(models.Model):
    code = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "{app_name}_{app_name}"

    def __str__(self):
        return self.code
"""
        CommonUtils.create_file_with_content(
            os.path.join(infra_dir, "models.py"), models_py, f"Created {app_name}/infrastructure/models.py"
        )

        repo_py = f"""from ..domain.entities import {pascal}Entity
from .models import {pascal}Model


class Django{pascal}Repository:
    def save(self, entity: {pascal}Entity) -> {pascal}Entity:
        obj, _ = {pascal}Model.objects.update_or_create(
            pk=entity.id,
            defaults={{"code": entity.code, "status": entity.status}},
        )
        return {pascal}Entity(id=obj.pk, code=obj.code, status=obj.status, created_at=obj.created_at)

    def get_by_code(self, code: str) -> {pascal}Entity | None:
        try:
            obj = {pascal}Model.objects.get(code=code)
            return {pascal}Entity(id=obj.pk, code=obj.code, status=obj.status, created_at=obj.created_at)
        except {pascal}Model.DoesNotExist:
            return None
"""
        CommonUtils.create_file_with_content(
            os.path.join(infra_dir, "repositories.py"), repo_py, f"Created {app_name}/infrastructure/repositories.py"
        )

        # Root models.py (re-export infrastructure models so Django discovers them for migrations)
        models_root = f"""from .infrastructure.models import {pascal}Model

__all__ = ["{pascal}Model"]
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models.py"), models_root, f"Created {app_name}/models.py"
        )

        # Layer 4: Presentation
        pres_dir = os.path.join(app_dir, "presentation")
        CommonUtils.create_directory_with_init(pres_dir, f"Created {app_name}/presentation/__init__.py")

        views_py = f"""from django.http import JsonResponse
from ..application.use_cases import Create{pascal}UseCase, Create{pascal}Command


def create_endpoint(request):
    code = request.GET.get("code", "sample-code")
    use_case = Create{pascal}UseCase()
    entity = use_case.execute(Create{pascal}Command(code=code))
    return JsonResponse({{"id": entity.id, "code": entity.code, "status": entity.status}})
"""
        CommonUtils.create_file_with_content(
            os.path.join(pres_dir, "views.py"), views_py, f"Created {app_name}/presentation/views.py"
        )

        urls_py = f"""from django.urls import path
from .presentation.views import create_endpoint

app_name = "{app_name}"

urlpatterns = [
    path("create/", create_endpoint, name="create"),
]
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "urls.py"), urls_py, f"Created {app_name}/urls.py")

        # Migrations & Admin & Tests
        migrations_dir = os.path.join(app_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        admin_py = f"""from django.contrib import admin
from .infrastructure.models import {pascal}Model

admin.site.register({pascal}Model)
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"), admin_py, f"Created {app_name}/admin.py"
        )

        tests_dir = os.path.join(app_dir, "tests")
        CommonUtils.create_directory_with_init(tests_dir, f"Created {app_name}/tests/__init__.py")

        test_code = f"""import pytest
from apps.{app_name}.application.use_cases import Create{pascal}UseCase, Create{pascal}Command


@pytest.mark.django_db
def test_create_{app_name}_use_case():
    use_case = Create{pascal}UseCase()
    entity = use_case.execute(Create{pascal}Command(code="ORDER-001"))
    assert entity.id is not None
    assert entity.code == "ORDER-001"
    assert entity.status == "draft"
"""
        CommonUtils.create_file_with_content(
            os.path.join(tests_dir, f"test_{app_name}.py"), test_code, f"Created {app_name}/tests/test_{app_name}.py"
        )

        return True


# ============================================================================
# 6. Clean Architecture
# ============================================================================
