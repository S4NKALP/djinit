#!/usr/bin/env python3
"""
Comprehensive test for all djinit features.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from djinit.creators.setup import SetupCreator

def create_project(name, metadata):
    """Create a test project."""
    test_dir = "/tmp/djinit_full_test"
    os.makedirs(test_dir, exist_ok=True)
    original_cwd = os.getcwd()

    try:
        os.chdir(test_dir)

        # Set defaults
        full_metadata = {
            "package_name": "backend",
            "use_github_actions": False,
            "use_gitlab_ci": False,
            "nested_apps": True,
            "nested_dir": "apps",
            "use_database_url": True,
            "database_type": "postgresql",
            "use_tailwind": False,
            "use_htmx": False,
            "use_docker": False,
            "use_vite": False,
            "predefined_structure": False,
            "unified_structure": False,
            "single_structure": False,
            "project_module_name": "config",
            **metadata
        }

        creator = SetupCreator(
            project_dir=name,
            project_name=name,
            primary_app="users",
            app_names=["users"],
            metadata=full_metadata
        )
        success = creator.create()
        return success, test_dir

    except Exception as e:
        print(f"  Error: {e}")
        return False, test_dir
    finally:
        os.chdir(original_cwd)


def verify_file(path, content_contains=None):
    """Verify a file exists and optionally check content."""
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    if content_contains:
        with open(path) as f:
            content = f.read()
        if content_contains not in content:
            return False, f"Content '{content_contains}' not found in {path}"
    return True, "OK"


def run_tests():
    print("=" * 70)
    print(" COMPREHENSIVE DJINIT TESTS")
    print("=" * 70)

    test_cases = [
        ("basic", {}, ["requirements.txt"]),
        ("docker", {"use_docker": True}, ["Dockerfile", "docker-compose.yml"]),
        ("vite", {"use_vite": True}, ["vite.config.js", "package.json", "frontend/index.html"]),
        ("tailwind", {"use_tailwind": True}, ["requirements.txt"]),
        ("htmx", {"use_htmx": True}, ["requirements.txt"]),
        ("all_postgres", {"use_docker": True, "use_vite": True, "use_tailwind": True, "use_htmx": True, "database_type": "postgresql"}, ["Dockerfile", "docker-compose.yml", "vite.config.js"]),
        ("all_mysql", {"use_docker": True, "use_vite": True, "use_tailwind": True, "database_type": "mysql"}, ["Dockerfile", "docker-compose.yml", "vite.config.js"]),
    ]

    results = []

    for name, metadata, expected_files in test_cases:
        print(f"\n{'─' * 70}")
        print(f" Testing: {name}")
        print(f" Metadata: {metadata}")

        # Clean up
        import shutil
        test_dir = "/tmp/djinit_full_test"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        # Create project
        success, _ = create_project(name, metadata)

        if not success:
            results.append((name, False, "Project creation failed"))
            print(f"  ✗ Failed to create project")
            continue

        # Verify files
        project_dir = os.path.join(test_dir, name)
        all_passed = True
        errors = []

        for file in expected_files:
            file_path = os.path.join(project_dir, file)
            exists, msg = verify_file(file_path)
            if not exists:
                all_passed = False
                errors.append(msg)
                print(f"  ✗ {msg}")
            else:
                print(f"  ✓ {file}")

        # Special checks for vite
        if metadata.get("use_vite"):
            settings_path = os.path.join(project_dir, "config/settings/base.py")
            exists, msg = verify_file(settings_path, "django_vite")
            if not exists:
                all_passed = False
                errors.append("django_vite not in settings")
                print(f"  ✗ django_vite not in settings")
            else:
                print(f"  ✓ django_vite in settings")

            req_path = os.path.join(project_dir, "requirements.txt")
            exists, msg = verify_file(req_path, "django-vite")
            if not exists:
                all_passed = False
                errors.append("django-vite not in requirements")
                print(f"  ✗ django-vite not in requirements")
            else:
                print(f"  ✓ django-vite in requirements")

        # Special checks for docker
        if metadata.get("use_docker"):
            dockerfile_path = os.path.join(project_dir, "Dockerfile")
            db_type = metadata.get("database_type", "postgresql")
            if db_type == "mysql":
                exists, msg = verify_file(dockerfile_path, "default-libmysqlclient-dev")
                if not exists:
                    all_passed = False
                    print(f"  ✗ MySQL client not in Dockerfile")
                else:
                    print(f"  ✓ MySQL client in Dockerfile")
            else:
                exists, msg = verify_file(dockerfile_path, "libpq-dev")
                if not exists:
                    all_passed = False
                    print(f"  ✗ PostgreSQL client not in Dockerfile")
                else:
                    print(f"  ✓ PostgreSQL client in Dockerfile")

        if all_passed:
            results.append((name, True, "All checks passed"))
            print(f"  ✓ ALL CHECKS PASSED")
        else:
            results.append((name, False, "; ".join(errors)))
            print(f"  ✗ SOME CHECKS FAILED")

    # Summary
    print("\n" + "=" * 70)
    print(" SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, s, _ in results if s)
    total = len(results)

    for name, success, msg in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name} - {msg}")

    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print("\n  ⚠️  SOME TESTS FAILED!")


if __name__ == "__main__":
    run_tests()