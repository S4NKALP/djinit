#!/usr/bin/env python3
"""
Comprehensive test for all djinit features including pytest.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from djinit.creators.setup import SetupCreator  # noqa: E402


def create_project(name, metadata):
    """Create a test project."""
    test_dir = "/tmp/djinit_pytest_test"
    os.makedirs(test_dir, exist_ok=True)
    original_cwd = os.getcwd()

    try:
        os.chdir(test_dir)

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
            "use_pytest": False,
            "predefined_structure": False,
            "unified_structure": False,
            "single_structure": False,
            "project_module_name": "config",
            **metadata,
        }

        creator = SetupCreator(
            project_dir=name, project_name=name, primary_app="users", app_names=["users"], metadata=full_metadata
        )
        success = creator.create()
        return success, test_dir

    except Exception as e:
        print(f"  Error: {e}")
        import traceback

        traceback.print_exc()
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
    print(" DJINIT COMPREHENSIVE TESTS (WITH PYTEST)")
    print("=" * 70)

    test_cases = [
        ("basic", {}, ["requirements.txt"]),
        ("docker", {"use_docker": True}, ["Dockerfile", "docker-compose.yml"]),
        ("vite", {"use_vite": True}, ["vite.config.js", "package.json"]),
        ("pytest", {"use_pytest": True}, ["pytest.ini", "conftest.py"]),
        ("tailwind", {"use_tailwind": True}, ["requirements.txt"]),
        ("htmx", {"use_htmx": True}, ["requirements.txt"]),
        (
            "all_postgres",
            {"use_docker": True, "use_vite": True, "use_tailwind": True, "use_htmx": True, "use_pytest": True},
            ["Dockerfile", "vite.config.js", "pytest.ini"],
        ),
        (
            "all_mysql",
            {"use_docker": True, "use_vite": True, "use_tailwind": True, "use_pytest": True, "database_type": "mysql"},
            ["Dockerfile", "vite.config.js", "pytest.ini"],
        ),
    ]

    results = []

    for name, metadata, expected_files in test_cases:
        print(f"\n{'─' * 70}")
        print(f" Testing: {name}")
        print(f" Metadata: {metadata}")

        import shutil

        test_dir = "/tmp/djinit_pytest_test"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        success, _ = create_project(name, metadata)

        if not success:
            results.append((name, False, "Project creation failed"))
            print("  ✗ Failed to create project")
            continue

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

        # Special checks for pytest
        if metadata.get("use_pytest"):
            req_path = os.path.join(project_dir, "requirements.txt")
            exists, msg = verify_file(req_path, "pytest")
            if not exists:
                all_passed = False
                print("  ✗ pytest not in requirements")
            else:
                print("  ✓ pytest in requirements")

            pytest_ini_path = os.path.join(project_dir, "pytest.ini")
            exists, msg = verify_file(pytest_ini_path, "DJANGO_SETTINGS_MODULE")
            if not exists:
                all_passed = False
                print("  ✗ DJANGO_SETTINGS_MODULE not in pytest.ini")
            else:
                print("  ✓ pytest.ini has DJANGO_SETTINGS_MODULE")

            conftest_path = os.path.join(project_dir, "conftest.py")
            exists, msg = verify_file(conftest_path, "pytest.fixture")
            if not exists:
                all_passed = False
                print("  ✗ pytest fixtures not in conftest.py")
            else:
                print("  ✓ conftest.py has fixtures")

        # Special checks for vite
        if metadata.get("use_vite"):
            settings_path = os.path.join(project_dir, "config/settings/base.py")
            exists, msg = verify_file(settings_path, "django_vite")
            if not exists:
                all_passed = False
                print("  ✗ django_vite not in settings")
            else:
                print("  ✓ django_vite in settings")

        # Special checks for docker
        if metadata.get("use_docker"):
            dockerfile_path = os.path.join(project_dir, "Dockerfile")
            db_type = metadata.get("database_type", "postgresql")
            if db_type == "mysql":
                exists, msg = verify_file(dockerfile_path, "default-libmysqlclient-dev")
                if not exists:
                    all_passed = False
                    print("  ✗ MySQL client not in Dockerfile")
                else:
                    print("  ✓ MySQL client in Dockerfile")
            else:
                exists, msg = verify_file(dockerfile_path, "libpq-dev")
                if not exists:
                    all_passed = False
                    print("  ✗ PostgreSQL client not in Dockerfile")
                else:
                    print("  ✓ PostgreSQL client in Dockerfile")

        if all_passed:
            results.append((name, True, "All checks passed"))
            print("  ✓ ALL CHECKS PASSED")
        else:
            results.append((name, False, "; ".join(errors)))
            print("  ✗ SOME CHECKS FAILED")

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
