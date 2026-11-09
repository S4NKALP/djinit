from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class MultiTenantHandler(ArchitectureHandler):
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

        # Common tenancy kernel
        tenancy_dir = os.path.join(root, "tenancy")
        CommonUtils.create_directory_with_init(tenancy_dir, "Created tenancy/__init__.py")

        models_py = '''import uuid
from django.db import models
from django.conf import settings


class Tenant(models.Model):
    """Organization/tenant entity for shared-schema multi-tenancy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    """User membership within a tenant organization."""

    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user")


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    pass


class TenantAwareModel(models.Model):
    """Abstract model enforcing strict tenant isolation."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)s_set")

    objects = TenantManager()

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """Abstract base model providing sort order and active status."""

    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ("sort_order", "id")
'''
        CommonUtils.create_file_with_content(
            os.path.join(tenancy_dir, "models.py"), models_py, "Created tenancy/models.py"
        )

        middleware_py = '''import uuid
from django.db.models import Q
from .models import Tenant


class TenantMiddleware:
    """Resolve current tenant from HTTP header (X-Tenant-ID) or query param."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get("X-Tenant-ID") or request.GET.get("tenant_id")
        request.tenant = None
        if tenant_id:
            try:
                try:
                    uuid_val = uuid.UUID(str(tenant_id))
                    q_filter = Q(id=uuid_val)
                except (ValueError, TypeError, AttributeError):
                    q_filter = Q(slug=tenant_id)

                request.tenant = Tenant.objects.filter(is_active=True).filter(q_filter).first()
            except Exception:
                request.tenant = None

        return self.get_response(request)
'''
        CommonUtils.create_file_with_content(
            os.path.join(tenancy_dir, "middleware.py"), middleware_py, "Created tenancy/middleware.py"
        )

        # apps.py for tenancy app
        tenancy_apps = """from django.apps import AppConfig


class TenancyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tenancy"
"""
        CommonUtils.create_file_with_content(
            os.path.join(tenancy_dir, "apps.py"), tenancy_apps, "Created tenancy/apps.py"
        )

        migrations_dir = os.path.join(tenancy_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, "Created tenancy/migrations/__init__.py")

        apps_dir = os.path.join(root, "apps")
        CommonUtils.create_directory_with_init(apps_dir, "Created apps/__init__.py")

        initial_apps = file_creator.app_names or ["projects"]
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

        # Tenant-aware models
        models_py = f"""from django.db import models
from tenancy.models import TenantAwareModel


class {pascal}(TenantAwareModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{{self.tenant.slug}}] {{self.title}}"
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models.py"), models_py, f"Created {app_name}/models.py"
        )

        # Tenant-isolated services
        services_py = f'''from tenancy.models import Tenant
from .models import {pascal}


def create_tenant_{app_name}(*, tenant: Tenant, title: str, description: str = "") -> {pascal}:
    """Create a new {app_name} strictly scoped to tenant."""
    item = {pascal}(tenant=tenant, title=title, description=description)
    item.full_clean()
    item.save()
    return item


def list_tenant_{app_name}(*, tenant: Tenant):
    """Retrieve items guaranteed not to leak cross-tenant data."""
    return {pascal}.objects.for_tenant(tenant)
'''
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "services.py"), services_py, f"Created {app_name}/services.py"
        )

        # Views
        views_py = f"""from django.http import JsonResponse
from .services import list_tenant_{app_name}


def index(request):
    tenant = getattr(request, "tenant", None)
    if not tenant:
        return JsonResponse({{"error": "Tenant header missing or invalid"}}, status=400)

    items = list_tenant_{app_name}(tenant=tenant)
    return JsonResponse({{"tenant": tenant.slug, "items": [i.title for i in items]}})
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "views.py"), views_py, f"Created {app_name}/views.py"
        )

        # URLs
        urls_py = f"""from django.urls import path
from .views import index

app_name = "{app_name}"

urlpatterns = [
    path("", index, name="index"),
]
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "urls.py"), urls_py, f"Created {app_name}/urls.py")

        # Migrations & Admin & Isolation Tests
        migrations_dir = os.path.join(app_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        admin_py = f"""from django.contrib import admin
from .models import {pascal}

admin.site.register({pascal})
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"), admin_py, f"Created {app_name}/admin.py"
        )

        tests_dir = os.path.join(app_dir, "tests")
        CommonUtils.create_directory_with_init(tests_dir, f"Created {app_name}/tests/__init__.py")

        test_code = f"""import pytest
from tenancy.models import Tenant
from apps.{app_name}.services import create_tenant_{app_name}, list_tenant_{app_name}


@pytest.mark.django_db
def test_tenant_isolation():
    tenant_a = Tenant.objects.create(name="Org A", slug="org-a")
    tenant_b = Tenant.objects.create(name="Org B", slug="org-b")

    item_a = create_tenant_{app_name}(tenant=tenant_a, title="Secret Project A")
    item_b = create_tenant_{app_name}(tenant=tenant_b, title="Secret Project B")

    items_for_a = list_tenant_{app_name}(tenant=tenant_a)
    assert item_a in items_for_a
    assert item_b not in items_for_a  # Crucial: verify cross-tenant isolation
"""
        CommonUtils.create_file_with_content(
            os.path.join(tests_dir, "test_isolation.py"), test_code, f"Created {app_name}/tests/test_isolation.py"
        )

        return True
