from __future__ import annotations

import os
from typing import TYPE_CHECKING

from djinit.creators.architectures.base import ArchitectureHandler
from djinit.utils.common import CommonUtils

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class FullStackHTMXHandler(ArchitectureHandler):
    @classmethod
    def scaffold_project(cls, file_creator: FileCreator) -> None:
        root = file_creator.project_root
        module_name = file_creator.module_name or "config"
        config_dir = os.path.join(root, module_name)
        settings_dir = os.path.join(config_dir, "settings")

        CommonUtils.create_directory_with_init(config_dir, f"Created {module_name}/__init__.py")
        CommonUtils.create_directory_with_init(settings_dir, f"Created {module_name}/settings/__init__.py")

        # HTMX and Tailwind enabled by default for this preset
        file_creator.metadata["use_htmx"] = True
        file_creator.metadata["use_tailwind"] = True

        base_ctx = {
            "project_name": module_name,
            "app_names": [],
            "use_database_url": file_creator.metadata.get("use_database_url", False),
            "database_type": file_creator.metadata.get("database_type", "sqlite3"),
            "use_tailwind": True,
            "use_htmx": True,
            "use_vite": False,
        }
        file_creator._create_settings_package(settings_dir, base_ctx, module_name)
        file_creator._create_lifecycle_files(config_dir, module_name, api_module=None)

        # Templates structure
        templates_dir = os.path.join(root, "templates")
        for sub in ["layouts", "components", "includes"]:
            os.makedirs(os.path.join(templates_dir, sub), exist_ok=True)

        # Base Layout with HTMX + Tailwind + optional Alpine.js
        base_html = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Django HTMX Application{% endblock %}</title>
    <!-- Tailwind CSS / DaisyUI -->
    <link rel="stylesheet" href="/static/css/tailwind.min.css">
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <!-- Alpine.js (Optional lightweight reactivity) -->
    <script defer src="https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js"></script>
</head>
<body class="min-h-screen bg-base-100 text-base-content antialiased" hx-boost="true" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% include "components/navbar.html" %}

    <main class="container mx-auto px-4 py-8">
        {% include "includes/messages.html" %}
        {% block content %}{% endblock %}
    </main>

    {% include "components/footer.html" %}
</body>
</html>
"""
        CommonUtils.create_file_with_content(
            os.path.join(templates_dir, "layouts", "base.html"),
            base_html,
            "Created templates/layouts/base.html",
        )

        navbar_html = """<header class="navbar bg-base-200 border-b border-base-300 px-4">
    <div class="flex-1">
        <a href="/" class="btn btn-ghost text-xl font-bold">Django HTMX</a>
    </div>
    <div class="flex-none">
        <ul class="menu menu-horizontal px-1">
            <li><a href="/">Dashboard</a></li>
        </ul>
    </div>
</header>
"""
        CommonUtils.create_file_with_content(
            os.path.join(templates_dir, "components", "navbar.html"),
            navbar_html,
            "Created templates/components/navbar.html",
        )

        footer_html = """<footer class="footer footer-center p-4 bg-base-200 text-base-content mt-12">
    <aside>
        <p>Built with Django, HTMX, Tailwind CSS and Alpine.js</p>
    </aside>
</footer>
"""
        CommonUtils.create_file_with_content(
            os.path.join(templates_dir, "components", "footer.html"),
            footer_html,
            "Created templates/components/footer.html",
        )

        messages_html = """{% if messages %}
<div class="mb-6 space-y-2">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'info' }} shadow-md">
        <span>{{ message }}</span>
    </div>
    {% endfor %}
</div>
{% endif %}
"""
        CommonUtils.create_file_with_content(
            os.path.join(templates_dir, "includes", "messages.html"),
            messages_html,
            "Created templates/includes/messages.html",
        )

        # Static assets
        for sub in ["css", "js", "images"]:
            os.makedirs(os.path.join(root, "static", sub), exist_ok=True)

        apps_dir = os.path.join(root, "apps")
        CommonUtils.create_directory_with_init(apps_dir, "Created apps/__init__.py")

        initial_apps = file_creator.app_names or ["dashboard"]
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

        # Models
        models_py = f"""from django.db import models


class {pascal}Item(models.Model):
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "models.py"), models_py, f"Created {app_name}/models.py"
        )

        # Forms
        forms_py = f"""from django import forms
from .models import {pascal}Item


class {pascal}ItemForm(forms.ModelForm):
    class Meta:
        model = {pascal}Item
        fields = ["title"]
        widgets = {{
            "title": forms.TextInput(attrs={{
                "class": "input input-bordered w-full max-w-xs",
                "placeholder": "Enter new item title...",
            }})
        }}
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "forms.py"), forms_py, f"Created {app_name}/forms.py"
        )

        # Views with full page & HTMX partial support
        views_dir = os.path.join(app_dir, "views")
        CommonUtils.create_directory_with_init(views_dir, f"Created {app_name}/views/__init__.py")

        views_py = f"""from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from ..models import {pascal}Item
from ..forms import {pascal}ItemForm


def index(request):
    items = {pascal}Item.objects.all()
    form = {pascal}ItemForm()
    return render(request, "{app_name}/index.html", {{"items": items, "form": form}})


@require_http_methods(["POST"])
def create_item(request):
    form = {pascal}ItemForm(request.POST)
    if form.is_valid():
        item = form.save()
        if request.htmx:
            return render(request, "{app_name}/partials/item_row.html", {{"item": item}})
    items = {pascal}Item.objects.all()
    return render(request, "{app_name}/index.html", {{"items": items, "form": form}})


@require_http_methods(["POST"])
def toggle_item(request, pk):
    item = get_object_or_404({pascal}Item, pk=pk)
    item.is_completed = not item.is_completed
    item.save(update_fields=["is_completed"])
    if request.htmx:
        return render(request, "{app_name}/partials/item_row.html", {{"item": item}})
    return index(request)
"""
        CommonUtils.create_file_with_content(
            os.path.join(views_dir, "views.py"), views_py, f"Created {app_name}/views/views.py"
        )

        # Templates
        tpl_dir = os.path.join(app_dir, "templates", app_name)
        partials_dir = os.path.join(tpl_dir, "partials")
        os.makedirs(partials_dir, exist_ok=True)

        index_html = f"""{{% extends "layouts/base.html" %}}

{{% block title %}}{pascal} Dashboard{{% endblock %}}

{{% block content %}}
<div class="card bg-base-200 shadow-xl max-w-2xl mx-auto p-6">
    <h1 class="text-3xl font-extrabold mb-6">{pascal} Items</h1>

    <form hx-post="{{% url '{app_name}:create' %}}"
          hx-target="#item-list"
          hx-swap="afterbegin"
          hx-on::after-request="this.reset()"
          class="flex gap-2 mb-6">
        {{{{ form.title }}}}
        <button type="submit" class="btn btn-primary">Add</button>
    </form>

    <div id="item-list" class="divide-y divide-base-300">
        {{% for item in items %}}
            {{% include "{app_name}/partials/item_row.html" %}}
        {{% empty %}}
            <p class="py-4 text-base-content/60">No items yet. Add one above!</p>
        {{% endfor %}}
    </div>
</div>
{{% endblock %}}
"""
        CommonUtils.create_file_with_content(
            os.path.join(tpl_dir, "index.html"), index_html, f"Created {app_name}/templates/index.html"
        )

        row_html = f"""<div id="item-{{{{ item.id }}}}" class="flex items-center justify-between py-3">
    <span class="{{% if item.is_completed %}}line-through text-base-content/50{{% endif %}} font-medium">
        {{{{ item.title }}}}
    </span>
    <button hx-post="{{% url '{app_name}:toggle' item.id %}}"
            hx-target="#item-{{{{ item.id }}}}"
            hx-swap="outerHTML"
            class="btn btn-sm {{% if item.is_completed %}}btn-warning{{% else %}}btn-success{{% endif %}}">
        {{% if item.is_completed %}}Undo{{% else %}}Done{{% endif %}}
    </button>
</div>
"""
        CommonUtils.create_file_with_content(
            os.path.join(partials_dir, "item_row.html"), row_html, f"Created {app_name}/partials/item_row.html"
        )

        # urls.py
        app_urls = f"""from django.urls import path
from .views.views import index, create_item, toggle_item

app_name = "{app_name}"

urlpatterns = [
    path("", index, name="index"),
    path("create/", create_item, name="create"),
    path("toggle/<int:pk>/", toggle_item, name="toggle"),
]
"""
        CommonUtils.create_file_with_content(os.path.join(app_dir, "urls.py"), app_urls, f"Created {app_name}/urls.py")

        # admin.py & migrations
        admin_py = f"""from django.contrib import admin
from .models import {pascal}Item

admin.site.register({pascal}Item)
"""
        CommonUtils.create_file_with_content(
            os.path.join(app_dir, "admin.py"), admin_py, f"Created {app_name}/admin.py"
        )

        migrations_dir = os.path.join(app_dir, "migrations")
        CommonUtils.create_directory_with_init(migrations_dir, f"Created {app_name}/migrations/__init__.py")

        # tests
        tests_dir = os.path.join(app_dir, "tests")
        CommonUtils.create_directory_with_init(tests_dir, f"Created {app_name}/tests/__init__.py")

        test_code = f"""import pytest
from django.urls import reverse
from apps.{app_name}.models import {pascal}Item


@pytest.mark.django_db
def test_htmx_create_item(client):
    url = reverse("{app_name}:create")
    response = client.post(url, {{"title": "Test HTMX Task"}}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert "Test HTMX Task" in response.content.decode()
    assert {pascal}Item.objects.filter(title="Test HTMX Task").exists()
"""
        CommonUtils.create_file_with_content(
            os.path.join(tests_dir, "test_views.py"), test_code, f"Created {app_name}/tests/test_views.py"
        )

        return True


# ============================================================================
# 4. Lightweight Architecture
# ============================================================================
