from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class ServiceLayerHandler(ArchitectureHandler):
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
            "use_tailwind": file_creator.metadata.get("use_tailwind", False),
            "use_htmx": file_creator.metadata.get("use_htmx", False),
            "use_vite": file_creator.metadata.get("use_vite", False),
        }
        file_creator._create_settings_package(settings_dir, base_ctx, module_name)
        file_creator._create_lifecycle_files(config_dir, module_name, api_module=None)

        apps_dir = os.path.join(root, "apps")
        CommonUtils.create_directory_with_init(apps_dir, "Created apps/__init__.py")

        initial_apps = file_creator.app_names or ["products", "core"]
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
    verbose_name = "{pascal}"
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "apps.py"), apps_py, f"Created {app_name}/apps.py")

        # models.py
        models_py = f"""from django.db import models


class {pascal}(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models.py"), models_py, f"Created {app_name}/models.py"
        )

        # services.py (business operations and transactions)
        services_py = f'''from decimal import Decimal
from django.db import transaction
from .models import {pascal}


@transaction.atomic
def create_{app_name}(*, name: str, description: str = "", price: Decimal | float = 0.0) -> {pascal}:
    """Service to create {app_name} with business validation."""
    if Decimal(str(price)) < 0:
        raise ValueError("Price cannot be negative")

    instance = {pascal}(name=name, description=description, price=price)
    instance.full_clean()
    instance.save()
    return instance


@transaction.atomic
def deactivate_{app_name}(instance: {pascal}) -> {pascal}:
    """Deactivate an active {app_name}."""
    instance.is_active = False
    instance.save(update_fields=["is_active", "updated_at"])
    return instance
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "services.py"), services_py, f"Created {app_name}/services.py"
        )

        # selectors.py (optimized read queries)
        selectors_py = f'''from django.db.models import QuerySet
from .models import {pascal}


def get_active_{app_name}_list() -> QuerySet[{pascal}]:
    """Retrieve all active {app_name} records."""
    return {pascal}.objects.filter(is_active=True)


def get_{app_name}_by_id(pk: int) -> {pascal} | None:
    """Fetch {app_name} by id or return None."""
    return {pascal}.objects.filter(pk=pk).first()
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "selectors.py"), selectors_py, f"Created {app_name}/selectors.py"
        )

        # forms.py
        forms_py = f"""from django import forms
from .models import {pascal}


class {pascal}Form(forms.ModelForm):
    class Meta:
        model = {pascal}
        fields = ["name", "description", "price"]
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "forms.py"), forms_py, f"Created {app_name}/forms.py"
        )

        # views.py
        views_py = f"""from django.http import JsonResponse
from .selectors import get_active_{app_name}_list


def index(request):
    items = get_active_{app_name}_list()
    return JsonResponse({{"count": items.count(), "{app_name}": [i.name for i in items[:10]]}})
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "views.py"), views_py, f"Created {app_name}/views.py"
        )

        # api/
        api_dir = os.path.join(app_dir, "api")
        CommonUtils.create_directory_with_init(api_dir, f"Created {app_name}/api/__init__.py")

        api_serializers = f"""from rest_framework import serializers
from ..models import {pascal}


class {pascal}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {pascal}
        fields = ["id", "name", "description", "price", "is_active", "created_at"]
"""
        CommonUtils.create_file_with_content(
            os.path.join(api_dir, "serializers.py"), api_serializers, f"Created {app_name}/api/serializers.py"
        )

        api_views = f"""from rest_framework import viewsets
from ..models import {pascal}
from .serializers import {pascal}Serializer


class {pascal}ViewSet(viewsets.ModelViewSet):
    queryset = {pascal}.objects.all()
    serializer_class = {pascal}Serializer
"""
        CommonUtils.create_file_with_content(
            os.path.join(api_dir, "views.py"), api_views, f"Created {app_name}/api/views.py"
        )

        api_urls = f"""from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import {pascal}ViewSet

router = DefaultRouter()
router.register(r"", {pascal}ViewSet, basename="{app_name}")

urlpatterns = [
    path("", include(router.urls)),
]
"""
        CommonUtils.create_file_with_content(
            os.path.join(api_dir, "urls.py"), api_urls, f"Created {app_name}/api/urls.py"
        )

        # urls.py
        app_urls = f"""from django.urls import include, path
from .views import index

app_name = "{app_name}"

urlpatterns = [
    path("", index, name="index"),
    path("api/", include("apps.{app_name}.api.urls")),
]
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "urls.py"), app_urls, f"Created {app_name}/urls.py")

        # admin.py
        admin_py = f"""from django.contrib import admin
from .models import {pascal}

admin.site.register({pascal})
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"), admin_py, f"Created {app_name}/admin.py"
        )

        # migrations & tests
        migrations_dir = os.path.join(app_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        tests_dir = os.path.join(app_dir, "tests")
        CommonUtils.create_directory_with_init(tests_dir, f"Created {app_name}/tests/__init__.py")
        test_code = f"""import pytest
from apps.{app_name}.services import create_{app_name}
from apps.{app_name}.selectors import get_active_{app_name}_list


@pytest.mark.django_db
def test_{app_name}_service_and_selector():
    item = create_{app_name}(name="Service Item", price=19.99)
    assert item.pk is not None
    assert get_active_{app_name}_list().filter(pk=item.pk).exists()
"""
        CommonUtils.create_file_with_content(
            os.path.join(tests_dir, f"test_{app_name}.py"), test_code, f"Created {app_name}/tests/test_{app_name}.py"
        )

        return True


# ============================================================================
# 3. Full-Stack HTMX Architecture
# ============================================================================
