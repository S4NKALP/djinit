#!/usr/bin/env python3
"""
Bug detection and checking script for djinit.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from djinit.templater import template_engine


def check_template_consistency():
    """Check if all templates have consistent variable syntax."""
    print("=" * 70)
    print(" CHECKING TEMPLATE CONSISTENCY")
    print("=" * 70)

    templates = [
        "project/Dockerfile-tpl",
        "project/docker-compose.yml-tpl",
        "project/vite.config.js-tpl",
        "project/package.json-tpl",
        "project/requirements-tpl",
        "config/settings/base.py-tpl",
    ]

    issues = []

    for tpl in templates:
        try:
            # Just try to render with empty context to see if it parses
            # Using [[ var ]] syntax
            content = template_engine.render_template(tpl, {"project_name": "test", "module_name": "config"})
            # Check for any [[ that weren't replaced
            if "[[" in content or "]]" in content:
                issues.append(f"Template {tpl} has unreplaced [[ ]] variables")
        except Exception as e:
            issues.append(f"Template {tpl} error: {e}")

    return issues


def check_metadata_usage():
    """Check if all metadata fields are used in templates."""
    print("\n" + "=" * 70)
    print(" CHECKING METADATA USAGE")
    print("=" * 70)

    metadata_fields = [
        "use_docker",
        "use_vite",
        "use_tailwind",
        "use_htmx",
        "use_database_url",
        "database_type",
    ]

    # Check requirements template
    req_template = "project/requirements-tpl"
    req_content = open(os.path.join(os.path.dirname(__file__), "..", "src/djinit/templates", req_template)).read()

    issues = []
    for field in metadata_fields:
        if f"use_{field}" in str(metadata_fields) or field in req_content:
            # Check if the field is used in template
            if field not in req_content and field != "use_database_url":
                # Check conditional usage
                if f"@IF {field}" not in req_content and f"@IF use_{field}" not in req_content:
                    pass  # It's optional

    return issues


def check_all_use_cases():
    """Test all combinations to find issues."""
    print("\n" + "=" * 70)
    print(" CHECKING ALL USE CASES")
    print("=" * 70)

    use_cases = [
        {"name": "basic", "metadata": {}},
        {"name": "docker", "metadata": {"use_docker": True, "database_type": "postgresql"}},
        {"name": "vite", "metadata": {"use_vite": True}},
        {"name": "tailwind", "metadata": {"use_tailwind": True}},
        {"name": "htmx", "metadata": {"use_htmx": True}},
        {"name": "docker_mysql", "metadata": {"use_docker": True, "database_type": "mysql"}},
        {
            "name": "all",
            "metadata": {
                "use_docker": True,
                "use_vite": True,
                "use_tailwind": True,
                "use_htmx": True,
                "database_type": "postgresql",
            },
        },
    ]

    issues = []

    for case in use_cases:
        name = case["name"]
        md = case["metadata"]

        ctx = {"project_name": "test", "module_name": "config", "use_database_url": True, **md}

        # Check requirements
        try:
            req = template_engine.render_template("project/requirements-tpl", ctx)

            # Check for django-vite when use_vite is True
            if md.get("use_vite") and "django-vite" not in req:
                issues.append(f"{name}: django-vite missing in requirements")

            # Check for django-tailwind when use_tailwind is True
            if md.get("use_tailwind") and "django-tailwind-cli" not in req:
                issues.append(f"{name}: django-tailwind-cli missing in requirements")

            # Check for django-htmx when use_htmx is True
            if md.get("use_htmx") and "django-htmx" not in req:
                issues.append(f"{name}: django-htmx missing in requirements")

            # Check for mysqlclient when MySQL
            if md.get("database_type") == "mysql" and "mysqlclient" not in req:
                issues.append(f"{name}: mysqlclient missing in requirements")

            # Check for psycopg when PostgreSQL
            if md.get("database_type") != "mysql" and "psycopg" not in req:
                issues.append(f"{name}: psycopg missing in requirements")

        except Exception as e:
            issues.append(f"{name}: requirements error - {e}")

        # Check Dockerfile for MySQL client
        if md.get("database_type") == "mysql" and md.get("use_docker"):
            try:
                dockerfile = template_engine.render_template("project/Dockerfile-tpl", ctx)
                if "default-libmysqlclient-dev" not in dockerfile and "mysqlclient" not in dockerfile:
                    issues.append(f"{name}: MySQL client missing in Dockerfile")
            except Exception as e:
                issues.append(f"{name}: Dockerfile error - {e}")

    return issues


def check_settings():
    """Check settings templates for correct conditional includes."""
    print("\n" + "=" * 70)
    print(" CHECKING SETTINGS")
    print("=" * 70)

    issues = []

    test_cases = [
        {"use_vite": True, "use_tailwind": False, "use_htmx": False},
        {"use_vite": False, "use_tailwind": True, "use_htmx": False},
        {"use_vite": False, "use_tailwind": False, "use_htmx": True},
        {"use_vite": True, "use_tailwind": True, "use_htmx": True},
    ]

    for ctx in test_cases:
        full_ctx = {"project_name": "config", "app_names": [], **ctx}
        try:
            settings = template_engine.render_template("config/settings/base.py-tpl", full_ctx)

            # Check django_vite
            if ctx.get("use_vite") and "django_vite" not in settings:
                issues.append(f"settings with {ctx}: django_vite missing")

            if ctx.get("use_vite") and "DJANGO_VITE" not in settings:
                issues.append(f"settings with {ctx}: DJANGO_VITE config missing")

            # Check django_tailwind
            if ctx.get("use_tailwind") and "django_tailwind_cli" not in settings:
                issues.append(f"settings with {ctx}: django_tailwind_cli missing")

            # Check django_htmx
            if ctx.get("use_htmx") and "django_htmx" not in settings:
                issues.append(f"settings with {ctx}: django_htmx missing")

        except Exception as e:
            issues.append(f"settings error with {ctx}: {e}")

    return issues


def check_vite_templates():
    """Check vite/frontend templates."""
    print("\n" + "=" * 70)
    print(" CHECKING VITE/FRONTEND TEMPLATES")
    print("=" * 70)

    ctx = {"project_name": "test", "module_name": "config"}
    templates = [
        "project/vite.config.js-tpl",
        "project/package.json-tpl",
        "project/frontend/index.html-tpl",
        "project/frontend/src/main.jsx-tpl",
        "project/frontend/src/App.jsx-tpl",
        "project/frontend/src/index.css-tpl",
    ]

    issues = []

    for tpl in templates:
        try:
            content = template_engine.render_template(tpl, ctx)
            # Check for unreplaced variables
            if "[[" in content:
                issues.append(f"{tpl}: has unreplaced [[ variables")
        except Exception as e:
            issues.append(f"{tpl}: error - {e}")

    return issues


def main():
    print("DJINIT BUG CHECK")
    print("=" * 70)

    all_issues = []

    # Run all checks
    all_issues.extend(check_template_consistency())
    all_issues.extend(check_metadata_usage())
    all_issues.extend(check_all_use_cases())
    all_issues.extend(check_settings())
    all_issues.extend(check_vite_templates())

    # Report
    print("\n" + "=" * 70)
    print(" BUG CHECK SUMMARY")
    print("=" * 70)

    if all_issues:
        print(f"\nFound {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  ✗ {issue}")
    else:
        print("\n  ✓ No issues found!")

    print("\n" + "=" * 70)
    print(" COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
