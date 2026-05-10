#!/usr/bin/env python3
"""
Comprehensive test for ALL djinit features and use cases.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import shutil

from djinit.creators.setup import SetupCreator


def create_project(name, metadata, structure="standard"):
    test_dir = "/tmp/djinit_full_test"
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
            "use_vue": False,
            "use_pytest": False,
            "predefined_structure": False,
            "unified_structure": False,
            "single_structure": False,
            "project_module_name": "config",
            **metadata
        }

        # Handle different structures
        if structure == "predefined":
            full_metadata["predefined_structure"] = True
            full_metadata["project_module_name"] = "config"
            full_metadata["nested_apps"] = True
            full_metadata["nested_dir"] = "apps"
            app_names = ["users", "core"]
        elif structure == "unified":
            full_metadata["unified_structure"] = True
            full_metadata["project_module_name"] = "core"
            full_metadata["nested_apps"] = True
            full_metadata["nested_dir"] = "apps"
            app_names = []
        elif structure == "single":
            full_metadata["single_structure"] = True
            full_metadata["project_module_name"] = name
            full_metadata["nested_apps"] = False
            full_metadata["nested_dir"] = None
            app_names = []
        else:  # standard
            full_metadata["project_module_name"] = "config"
            app_names = ["users"]

        creator = SetupCreator(
            project_dir=name,
            project_name=name,
            primary_app=app_names[0] if app_names else "users",
            app_names=app_names,
            metadata=full_metadata
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
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    if content_contains:
        with open(path) as f:
            content = f.read()
        if content_contains not in content:
            return False, f"Content '{content_contains}' not found in {path}"
    return True, "OK"


def run_all_tests():
    print("=" * 70)
    print(" DJINIT - COMPLETE TEST SUITE")
    print("=" * 70)

    # All test cases: (name, structure, metadata, expected_files, extra_checks)
    test_cases = [
        # Basic tests
        ("basic_std", "standard", {}, ["requirements.txt"], []),
        ("basic_pre", "predefined", {}, ["requirements.txt"], []),
        ("basic_uni", "unified", {}, ["requirements.txt"], []),
        ("basic_sgl", "single", {}, ["requirements.txt"], []),

        # Single features
        ("docker", "standard", {"use_docker": True, "database_type": "postgresql"}, ["Dockerfile", "docker-compose.yml"], ["postgres"]),
        ("docker_mysql", "standard", {"use_docker": True, "database_type": "mysql"}, ["Dockerfile", "docker-compose.yml"], ["mysql"]),
        ("react", "standard", {"use_vite": True}, ["vite.config.js", "package.json"], ["react"]),
        ("vue", "standard", {"use_vue": True}, ["vite.config.js", "package.json"], ["vue"]),
        ("tailwind", "standard", {"use_tailwind": True}, ["requirements.txt"], ["tailwind"]),
        ("htmx", "standard", {"use_htmx": True}, ["requirements.txt"], ["htmx"]),
        ("pytest", "standard", {"use_pytest": True}, ["pytest.ini", "conftest.py"], ["pytest"]),

        # Combinations
        ("docker_react", "standard", {"use_docker": True, "use_vite": True, "database_type": "postgresql"}, ["Dockerfile", "vite.config.js"], ["postgres", "react"]),
        ("docker_vue", "standard", {"use_docker": True, "use_vue": True, "database_type": "postgresql"}, ["Dockerfile", "vite.config.js"], ["postgres", "vue"]),
        ("react_pytest", "standard", {"use_vite": True, "use_pytest": True}, ["vite.config.js", "pytest.ini"], ["react", "pytest"]),
        ("vue_pytest", "standard", {"use_vue": True, "use_pytest": True}, ["vite.config.js", "pytest.ini"], ["vue", "pytest"]),
        ("tailwind_htmx", "standard", {"use_tailwind": True, "use_htmx": True}, ["requirements.txt"], ["tailwind", "htmx"]),

        # All features
        ("all_postgres", "standard", {
            "use_docker": True, "use_vite": True, "use_tailwind": True,
            "use_htmx": True, "use_pytest": True, "database_type": "postgresql"
        }, ["Dockerfile", "vite.config.js", "pytest.ini"], ["postgres", "react", "pytest"]),

        ("all_mysql", "standard", {
            "use_docker": True, "use_vue": True, "use_tailwind": True,
            "use_pytest": True, "database_type": "mysql"
        }, ["Dockerfile", "vite.config.js", "pytest.ini"], ["mysql", "vue", "pytest"]),

        # Structure tests with features
        ("predefined_docker", "predefined", {"use_docker": True, "database_type": "postgresql"}, ["Dockerfile"], ["postgres"]),
        ("predefined_vue", "predefined", {"use_vue": True}, ["vite.config.js"], ["vue"]),
        ("unified_docker", "unified", {"use_docker": True, "database_type": "postgresql"}, ["Dockerfile"], ["postgres"]),
        ("unified_vue", "unified", {"use_vue": True}, ["vite.config.js"], ["vue"]),
        ("single_docker", "single", {"use_docker": True, "database_type": "postgresql"}, ["Dockerfile"], ["postgres"]),
        ("single_vue", "single", {"use_vue": True}, ["vite.config.js"], ["vue"]),
    ]

    results = []

    for name, structure, metadata, expected_files, extra_checks in test_cases:
        print(f"\n{'─' * 70}")
        print(f" Testing: {name} (structure: {structure})")
        print(f" Features: {list(metadata.keys()) if metadata else ['basic']}")

        test_dir = "/tmp/djinit_full_test"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        success, _ = create_project(name, metadata, structure)

        if not success:
            results.append((name, False, "Project creation failed"))
            print("  ✗ Failed to create project")
            continue

        project_dir = os.path.join(test_dir, name)
        all_passed = True
        errors = []

        # Check expected files
        for file in expected_files:
            file_path = os.path.join(project_dir, file)
            exists, msg = verify_file(file_path)
            if not exists:
                all_passed = False
                errors.append(msg)
                print(f"  ✗ {msg}")
            else:
                print(f"  ✓ {file}")

        # Run extra checks
        for check in extra_checks:
            if check == "postgres":
                dockerfile_path = os.path.join(project_dir, "Dockerfile")
                exists, _ = verify_file(dockerfile_path, "libpq-dev")
                if not exists:
                    all_passed = False
                    print("  ✗ PostgreSQL client missing in Dockerfile")
                else:
                    print("  ✓ PostgreSQL in Dockerfile")

            elif check == "mysql":
                dockerfile_path = os.path.join(project_dir, "Dockerfile")
                exists, _ = verify_file(dockerfile_path, "default-libmysqlclient-dev")
                if not exists:
                    all_passed = False
                    print("  ✗ MySQL client missing in Dockerfile")
                else:
                    print("  ✓ MySQL in Dockerfile")

            elif check == "react":
                pkg_path = os.path.join(project_dir, "package.json")
                exists, _ = verify_file(pkg_path, "react")
                if not exists:
                    all_passed = False
                    print("  ✗ React not in package.json")
                else:
                    print("  ✓ React in package.json")

            elif check == "vue":
                pkg_path = os.path.join(project_dir, "package.json")
                exists, _ = verify_file(pkg_path, "vue")
                if not exists:
                    all_passed = False
                    print("  ✗ Vue not in package.json")
                else:
                    print("  ✓ Vue in package.json")

                vue_file = os.path.join(project_dir, "frontend/src/App.vue")
                exists, _ = verify_file(vue_file)
                if not exists:
                    all_passed = False
                    print("  ✗ App.vue not found")
                else:
                    print("  ✓ App.vue found")

            elif check == "pytest":
                req_path = os.path.join(project_dir, "requirements.txt")
                exists, _ = verify_file(req_path, "pytest")
                if not exists:
                    all_passed = False
                    print("  ✗ pytest not in requirements")
                else:
                    print("  ✓ pytest in requirements")

                pytest_path = os.path.join(project_dir, "pytest.ini")
                exists, _ = verify_file(pytest_path, "DJANGO_SETTINGS_MODULE")
                if not exists:
                    all_passed = False
                    print("  ✗ pytest.ini incomplete")
                else:
                    print("  ✓ pytest.ini configured")

            elif check == "tailwind":
                req_path = os.path.join(project_dir, "requirements.txt")
                exists, _ = verify_file(req_path, "django-tailwind-cli")
                if not exists:
                    all_passed = False
                    print("  ✗ Tailwind not in requirements")
                else:
                    print("  ✓ Tailwind in requirements")

            elif check == "htmx":
                req_path = os.path.join(project_dir, "requirements.txt")
                exists, _ = verify_file(req_path, "django-htmx")
                if not exists:
                    all_passed = False
                    print("  ✗ HTMX not in requirements")
                else:
                    print("  ✓ HTMX in requirements")

        if all_passed:
            results.append((name, True, "All checks passed"))
            print("  ✓ ALL CHECKS PASSED")
        else:
            results.append((name, False, "; ".join(errors)))
            print("  ✗ SOME CHECKS FAILED")

    # Summary
    print("\n" + "=" * 70)
    print(" FINAL SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, s, _ in results if s)
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()

    for name, success, _msg in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    print("\n" + "=" * 70)
    if passed == total:
        print(" 🎉 ALL TESTS PASSED! 🎉")
    else:
        print(" ⚠️  SOME TESTS FAILED!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
