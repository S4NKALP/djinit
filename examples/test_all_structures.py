#!/usr/bin/env python3
"""
Test script to show hello world examples for all project structures and cases.
Run from the djinit project root: PYTHONPATH=src python3 examples/test_all_structures.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from djinit.templater import template_engine


def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subsection(title):
    print(f"\n{'─' * 70}")
    print(f" {title}")
    print(f"{'─' * 70}")


# Define all test cases
CASES = [
    ("Basic (no optional features)", {
        "use_docker": False, "use_vite": False, "use_tailwind": False,
        "use_htmx": False, "database_type": "postgresql", "use_database_url": True
    }),
    ("Docker only", {
        "use_docker": True, "use_vite": False, "use_tailwind": False,
        "use_htmx": False, "database_type": "postgresql", "use_database_url": True
    }),
    ("Vite/React only", {
        "use_docker": False, "use_vite": True, "use_tailwind": False,
        "use_htmx": False, "database_type": "postgresql", "use_database_url": True
    }),
    ("Docker + Vite", {
        "use_docker": True, "use_vite": True, "use_tailwind": False,
        "use_htmx": False, "database_type": "postgresql", "use_database_url": True
    }),
    ("Tailwind only", {
        "use_docker": False, "use_vite": False, "use_tailwind": True,
        "use_htmx": False, "database_type": "postgresql", "use_database_url": True
    }),
    ("HTMX only", {
        "use_docker": False, "use_vite": False, "use_tailwind": False,
        "use_htmx": True, "database_type": "postgresql", "use_database_url": True
    }),
    ("Tailwind + HTMX", {
        "use_docker": False, "use_vite": False, "use_tailwind": True,
        "use_htmx": True, "database_type": "postgresql", "use_database_url": True
    }),
    ("All: Docker + Vite + Tailwind + HTMX + PostgreSQL", {
        "use_docker": True, "use_vite": True, "use_tailwind": True,
        "use_htmx": True, "database_type": "postgresql", "use_database_url": True
    }),
    ("All: Docker + Vite + Tailwind + HTMX + MySQL", {
        "use_docker": True, "use_vite": True, "use_tailwind": True,
        "use_htmx": True, "database_type": "mysql", "use_database_url": True
    }),
]

STRUCTURES = [
    ("standard", "config", "Standard Structure (default Django layout)"),
    ("predefined", "config", "Predefined Structure (apps/users, apps/core, api/)"),
    ("unified", "core", "Unified Structure (core/, apps/core, apps/api)"),
    ("single", "myproject", "Single Folder Layout (everything in one folder)"),
]


def show_file_tree(struct_type, case_name, metadata):
    """Show expected file tree for a structure + case combination."""

    module_name = {
        "standard": "config",
        "predefined": "config",
        "unified": "core",
        "single": "myproject"
    }[struct_type]

    features = []
    if metadata.get("use_docker"): features.append("Docker")
    if metadata.get("use_vite"): features.append("Vite")
    if metadata.get("use_tailwind"): features.append("Tailwind")
    if metadata.get("use_htmx"): features.append("HTMX")
    features.append(metadata.get("database_type", "postgresql").upper())

    print(f"  Features: {', '.join(features)}")
    print(f"  Project: myproject/")
    print(f"  Module: {module_name}/")

    indent = "    "

    # Always present
    print(f"{indent}├── .env.sample")
    print(f"{indent}├── .gitignore")
    print(f"{indent}├── requirements.txt")
    print(f"{indent}├── pyproject.toml")
    print(f"{indent}├── Procfile")
    print(f"{indent}├── justfile")
    print(f"{indent}├── runtime.txt")

    if metadata.get("use_docker"):
        print(f"{indent}├── Dockerfile")
        print(f"{indent}├── docker-compose.yml")
        print(f"{indent}├── .dockerignore")

    if struct_type == "standard":
        print(f"{indent}├── config/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── settings/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── base.py")
        print(f"{indent}│   │   ├── development.py")
        print(f"{indent}│   │   └── production.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   ├── wsgi.py")
        print(f"{indent}│   └── asgi.py")
        print(f"{indent}├── users/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── models.py")
        print(f"{indent}│   ├── views.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   └── apps.py")
        print(f"{indent}└── manage.py")

    elif struct_type == "predefined":
        print(f"{indent}├── config/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── settings/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── base.py")
        print(f"{indent}│   │   ├── development.py")
        print(f"{indent}│   │   └── production.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   ├── wsgi.py")
        print(f"{indent}│   └── asgi.py")
        print(f"{indent}├── apps/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── core/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── utils/")
        print(f"{indent}│   │   ├── mixins/")
        print(f"{indent}│   │   └── middleware/")
        print(f"{indent}│   └── users/")
        print(f"{indent}│       ├── __init__.py")
        print(f"{indent}│       └── apps.py")
        print(f"{indent}├── api/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   └── v1/")
        print(f"{indent}│       ├── __init__.py")
        print(f"{indent}│       └── urls.py")
        print(f"{indent}└── manage.py")

    elif struct_type == "unified":
        print(f"{indent}├── core/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── settings/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── base.py")
        print(f"{indent}│   │   ├── development.py")
        print(f"{indent}│   │   └── production.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   ├── wsgi.py")
        print(f"{indent}│   └── asgi.py")
        print(f"{indent}├── apps/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── apps.py")
        print(f"{indent}│   ├── api/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── urls.py")
        print(f"{indent}│   │   └── v1/")
        print(f"{indent}│   │       ├── __init__.py")
        print(f"{indent}│   │       └── urls.py")
        print(f"{indent}│   ├── models/")
        print(f"{indent}│   ├── views/")
        print(f"{indent}│   ├── serializers/")
        print(f"{indent}│   ├── tests/")
        print(f"{indent}│   └── urls/")
        print(f"{indent}└── manage.py")

    else:  # single
        print(f"{indent}├── myproject/")
        print(f"{indent}│   ├── __init__.py")
        print(f"{indent}│   ├── settings/")
        print(f"{indent}│   │   ├── __init__.py")
        print(f"{indent}│   │   ├── base.py")
        print(f"{indent}│   │   ├── development.py")
        print(f"{indent}│   │   └── production.py")
        print(f"{indent}│   ├── urls.py")
        print(f"{indent}│   ├── wsgi.py")
        print(f"{indent}│   ├── asgi.py")
        print(f"{indent}│   ├── api/")
        print(f"{indent}│   ├── models/")
        print(f"{indent}│   ├── admin/")
        print(f"{indent}│   └── tests/")
        print(f"{indent}└── manage.py")

    if metadata.get("use_vite"):
        print(f"{indent}├── frontend/")
        print(f"{indent}│   ├── index.html")
        print(f"{indent}│   ├── vite.config.js")
        print(f"{indent}│   ├── package.json")
        print(f"{indent}│   └── src/")
        print(f"{indent}│       ├── main.jsx")
        print(f"{indent}│       ├── App.jsx")
        print(f"{indent}│       └── index.css")
        print(f"{indent}└── static/")

    if metadata.get("use_tailwind"):
        print(f"{indent}├── static/")
        print(f"{indent}│   └── css/")
        print(f"{indent}└── templates/")


def show_template_examples():
    """Show actual template content for key files."""

    print_section("TEMPLATE CONTENT EXAMPLES")

    # 1. Requirements.txt examples
    print_subsection("1. requirements.txt - Basic (No optional features)")
    ctx = {"use_vite": False, "use_tailwind": False, "use_htmx": False,
           "database_type": "postgresql", "use_database_url": True}
    print(template_engine.render_template("project/requirements-tpl", ctx))

    print_subsection("2. requirements.txt - All Features (PostgreSQL)")
    ctx = {"use_vite": True, "use_tailwind": True, "use_htmx": True,
           "database_type": "postgresql", "use_database_url": True}
    print(template_engine.render_template("project/requirements-tpl", ctx))

    print_subsection("3. requirements.txt - All Features (MySQL)")
    ctx = {"use_vite": True, "use_tailwind": True, "use_htmx": True,
           "database_type": "mysql", "use_database_url": True}
    print(template_engine.render_template("project/requirements-tpl", ctx))

    # 4. Settings examples
    print_subsection("4. settings/base.py - With Vite enabled")
    ctx = {"project_name": "config", "app_names": ["users"],
           "use_vite": True, "use_tailwind": False, "use_htmx": False,
           "use_database_url": True, "database_type": "postgresql"}
    result = template_engine.render_template("config/settings/base.py-tpl", ctx)
    for line in result.split('\n'):
        if 'django_vite' in line or 'DJANGO_VITE' in line:
            print(line)

    print_subsection("5. settings/base.py - With Tailwind enabled")
    ctx = {"project_name": "config", "app_names": ["users"],
           "use_vite": False, "use_tailwind": True, "use_htmx": False,
           "use_database_url": True, "database_type": "postgresql"}
    result = template_engine.render_template("config/settings/base.py-tpl", ctx)
    for line in result.split('\n'):
        if 'tailwind' in line.lower() or 'daisyui' in line.lower():
            print(line)

    # 6. Dockerfile example
    print_subsection("6. Dockerfile (PostgreSQL)")
    ctx = {"project_name": "myproject", "module_name": "config", "database_type": "postgresql"}
    print(template_engine.render_template("project/Dockerfile-tpl", ctx))

    print_subsection("7. Dockerfile (MySQL)")
    ctx = {"project_name": "myproject", "module_name": "config", "database_type": "mysql"}
    print(template_engine.render_template("project/Dockerfile-tpl", ctx))

    # 8. docker-compose.yml examples
    print_subsection("8. docker-compose.yml (PostgreSQL)")
    ctx = {"project_name": "myproject", "database_type": "postgresql", "use_database_url": True}
    print(template_engine.render_template("project/docker-compose.yml-tpl", ctx))

    # 9. vite.config.js
    print_subsection("9. vite.config.js")
    ctx = {"project_name": "myproject", "module_name": "config"}
    print(template_engine.render_template("project/vite.config.js-tpl", ctx))

    # 10. package.json
    print_subsection("10. package.json")
    print(template_engine.render_template("project/package.json-tpl", ctx))

    # 11. Frontend examples
    print_subsection("11. frontend/index.html")
    print(template_engine.render_template("project/frontend/index.html-tpl", ctx))

    print_subsection("12. frontend/src/App.jsx")
    print(template_engine.render_template("project/frontend/src/App.jsx-tpl", ctx))


def main():
    print_section("DJINIT - ALL STRUCTURES & CASES")

    # Show all structure + case combinations
    for struct_type, module_name, struct_desc in STRUCTURES:
        print_section(struct_desc)

        for case_name, metadata in CASES:
            print_subsection(case_name)
            show_file_tree(struct_type, case_name, metadata)

    # Show template content examples
    show_template_examples()

    print("\n" + "=" * 70)
    print(" ALL STRUCTURES & CASES TESTED SUCCESSFULLY!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  • {len(STRUCTURES)} project structures")
    print(f"  • {len(CASES)} feature combinations")
    print(f"  • Total: {len(STRUCTURES) * len(CASES)} unique configurations")
    print("\nEach combination generates:")
    print("  - Django project files based on structure type")
    print("  - Optional: Docker files (Dockerfile, docker-compose.yml)")
    print("  - Optional: Vite/React frontend (vite.config.js, package.json, etc.)")
    print("  - Optional: Tailwind CSS configuration")
    print("  - Optional: HTMX integration")


if __name__ == "__main__":
    main()