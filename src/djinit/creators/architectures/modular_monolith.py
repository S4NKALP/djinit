from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class ModularMonolithHandler(ArchitectureHandler):
    @classmethod
    def scaffold_project(cls, file_creator: FileCreator) -> None:
        root = file_creator.project_root
        module_name = file_creator.module_name or "config"
        config_dir = os.path.join(root, module_name)
        settings_dir = os.path.join(config_dir, "settings")

        # 1. Config & Settings
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

        # Testing settings
        CommonUtils.create_file_from_template(
            os.path.join(settings_dir, "testing.py"),
            "config/settings/testing.py-tpl",
            {},
            f"Created {module_name}/settings/testing.py",
        )

        file_creator._create_lifecycle_files(config_dir, module_name, api_module=None)

        # 2. Common Package (reusable kernel)
        common_dir = os.path.join(root, "common")
        CommonUtils.create_directory_with_init(common_dir, "Created common/__init__.py")
        for sub in ["db", "middleware", "permissions", "utils"]:
            CommonUtils.create_directory_with_init(os.path.join(common_dir, sub), f"Created common/{sub}/__init__.py")

        # Base DB Models
        db_models_code = '''import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model that tracks created and updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Standard base model combining UUID primary key and timestamp tracking."""

    class Meta:
        abstract = True
'''
        CommonUtils.create_file_with_content(
            os.path.join(common_dir, "db", "models.py"),
            db_models_code,
            "Created common/db/models.py",
        )

        # Common Permissions
        perms_code = '''from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission allowing access only to object owners or administrators."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        user_field = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return user_field == request.user
'''
        CommonUtils.create_file_with_content(
            os.path.join(common_dir, "permissions", "base.py"),
            perms_code,
            "Created common/permissions/base.py",
        )

        # Common Middleware
        middleware_code = '''import uuid


class RequestIDMiddleware:
    """Attach a unique correlation ID to every incoming request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = self.get_response(request)
        response["X-Request-ID"] = request.id
        return response
'''
        CommonUtils.create_file_with_content(
            os.path.join(common_dir, "middleware", "request_id.py"),
            middleware_code,
            "Created common/middleware/request_id.py",
        )

        # 3. Root Apps directory
        apps_dir = os.path.join(root, "apps")
        CommonUtils.create_directory_with_init(apps_dir, "Created apps/__init__.py")

        # 4. Root directories: templates, static, media, tests
        for dir_name in ["templates", "static", "media", "tests"]:
            target = os.path.join(root, dir_name)
            os.makedirs(target, exist_ok=True)
            if dir_name == "tests":
                CommonUtils.create_init_file(target, "Created tests/__init__.py")

        # 5. Scaffold initial apps
        initial_apps = file_creator.app_names or ["accounts", "core"]
        for app in initial_apps:
            cls.scaffold_app(app, apps_dir)

    @classmethod
    def scaffold_app(cls, app_name: str, apps_dir: str) -> bool:
        app_dir = os.path.join(apps_dir, app_name)
        os.makedirs(app_dir, exist_ok=True)
        CommonUtils.create_init_file(app_dir, f"Created {app_name}/__init__.py")

        pascal = app_name.title().replace("_", "")

        # apps.py
        apps_py = f'''from django.apps import AppConfig


class {pascal}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{app_name}"
    verbose_name = "{pascal}"
'''
        CommonUtils.create_file_with_content(os.path.join(app_dir, "apps.py"), apps_py, f"Created {app_name}/apps.py")

        # Package subfolders
        packages = ["models", "services", "selectors", "views", "api", "tests", "migrations"]
        for pkg in packages:
            CommonUtils.create_directory_with_init(os.path.join(app_dir, pkg), f"Created {app_name}/{pkg}/__init__.py")

        # Models
        models_code = f'''from django.db import models
from common.db.models import BaseModel


class {pascal}Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "{pascal} Item"
        verbose_name_plural = "{pascal} Items"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models", f"{app_name}.py"),
            models_code,
            f"Created {app_name}/models/{app_name}.py",
        )
        # Expose models in models/__init__.py for Django discovery
        models_init = f'''from .{app_name} import {pascal}Item

__all__ = ["{pascal}Item"]
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models", "__init__.py"),
            models_init,
            f"Created {app_name}/models/__init__.py",
        )

        # Services (operations, transactions)
        services_code = f'''from django.db import transaction
from ..models import {pascal}Item


@transaction.atomic
def create_{app_name}_item(*, name: str, description: str = "") -> {pascal}Item:
    """Create a new {app_name} item atomically."""
    item = {pascal}Item(name=name, description=description)
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def update_{app_name}_item(item: {pascal}Item, **fields) -> {pascal}Item:
    """Update fields on a {app_name} item atomically."""
    for key, value in fields.items():
        if hasattr(item, key):
            setattr(item, key, value)
    item.full_clean()
    item.save()
    return item
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "services", f"{app_name}_service.py"),
            services_code,
            f"Created {app_name}/services/{app_name}_service.py",
        )

        # Selectors (queries)
        selectors_code = f'''from django.db.models import QuerySet
from ..models import {pascal}Item


def list_{app_name}_items(*, is_active: bool | None = None) -> QuerySet[{pascal}Item]:
    """Retrieve filtered {app_name} items."""
    qs = {pascal}Item.objects.all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_{app_name}_item_by_id(item_id) -> {pascal}Item | None:
    """Retrieve single {app_name} item by primary key."""
    try:
        return {pascal}Item.objects.get(pk=item_id)
    except {pascal}Item.DoesNotExist:
        return None
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "selectors", f"{app_name}_selector.py"),
            selectors_code,
            f"Created {app_name}/selectors/{app_name}_selector.py",
        )

        # Views
        views_code = f'''from django.http import JsonResponse
from ..selectors.{app_name}_selector import list_{app_name}_items


def index(request):
    items = list_{app_name}_items(is_active=True)
    return JsonResponse({{"count": items.count(), "{app_name}": [i.name for i in items[:10]]}})
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "views", f"{app_name}_views.py"),
            views_code,
            f"Created {app_name}/views/{app_name}_views.py",
        )

        # API Serializers & Router
        api_serializers = f"""from rest_framework import serializers
from ..models import {pascal}Item


class {pascal}ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = {pascal}Item
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "api", "serializers.py"),
            api_serializers,
            f"Created {app_name}/api/serializers.py",
        )

        api_views = f"""from rest_framework import viewsets
from ..models import {pascal}Item
from .serializers import {pascal}ItemSerializer


class {pascal}ItemViewSet(viewsets.ModelViewSet):
    queryset = {pascal}Item.objects.all()
    serializer_class = {pascal}ItemSerializer
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "api", "views.py"),
            api_views,
            f"Created {app_name}/api/views.py",
        )

        api_urls = f'''from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import {pascal}ItemViewSet

router = DefaultRouter()
router.register(r"items", {pascal}ItemViewSet, basename="{app_name}-items")

urlpatterns = [
    path("", include(router.urls)),
]
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "api", "urls.py"),
            api_urls,
            f"Created {app_name}/api/urls.py",
        )

        # Root app urls.py
        app_urls = f'''from django.urls import include, path
from .views.{app_name}_views import index

app_name = "{app_name}"

urlpatterns = [
    path("", index, name="index"),
    path("api/", include("apps.{app_name}.api.urls")),
]
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "urls.py"),
            app_urls,
            f"Created {app_name}/urls.py",
        )

        # admin.py
        admin_py = f"""from django.contrib import admin
from .models import {pascal}Item


@admin.register({pascal}Item)
class {pascal}ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"),
            admin_py,
            f"Created {app_name}/admin.py",
        )

        # Tests
        test_services = f"""import pytest
from apps.{app_name}.services.{app_name}_service import create_{app_name}_item
from apps.{app_name}.selectors.{app_name}_selector import list_{app_name}_items


@pytest.mark.django_db
def test_create_and_list_{app_name}_item():
    item = create_{app_name}_item(name="Test Item", description="Testing service")
    assert item.pk is not None
    assert item.name == "Test Item"

    items = list_{app_name}_items(is_active=True)
    assert items.filter(pk=item.pk).exists()
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "tests", f"test_{app_name}_services.py"),
            test_services,
            f"Created {app_name}/tests/test_{app_name}_services.py",
        )

        return True


# ============================================================================
# 2. Service Layer Architecture
# ============================================================================
