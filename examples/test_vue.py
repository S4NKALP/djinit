#!/usr/bin/env python3
"""
Comprehensive test for all djinit features including Vue.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from djinit.creators.setup import SetupCreator


def create_project(name, metadata):
    test_dir = "/tmp/djinit_vue_test"
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


def run_tests():
    print("=" * 70)
    print(" DJINIT COMPREHENSIVE TESTS (WITH VUE)")
    print("=" * 70)

    test_cases = [
        ("basic", {}, ["requirements.txt"]),
        ("docker", {"use_docker": True}, ["Dockerfile"]),
        ("react", {"use_vite": True}, ["vite.config.js", "package.json"]),
        ("vue", {"use_vue": True}, ["vite.config.js", "package.json"]),
        ("pytest", {"use_pytest": True}, ["pytest.ini"]),
        ("all_react", {"use_docker": True, "use_vite": True, "use_pytest": True}, ["Dockerfile", "vite.config.js"]),
        ("all_vue", {"use_docker": True, "use_vue": True, "use_pytest": True}, ["Dockerfile", "vite.config.js"]),
    ]

    results = []

    for name, metadata, expected_files in test_cases:
        print(f"\n{'─' * 70}")
        print(f" Testing: {name}")
        print(f" Metadata: {metadata}")

        import shutil
        test_dir = "/tmp/djinit_vue_test"
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

        # Special checks for React
        if metadata.get("use_vite"):
            pkg_path = os.path.join(project_dir, "package.json")
            exists, msg = verify_file(pkg_path, "react")
            if not exists:
                all_passed = False
                print("  ✗ React not in package.json")
            else:
                print("  ✓ React in package.json")

        # Special checks for Vue
        if metadata.get("use_vue"):
            pkg_path = os.path.join(project_dir, "package.json")
            exists, msg = verify_file(pkg_path, "vue")
            if not exists:
                all_passed = False
                print("  ✗ Vue not in package.json")
            else:
                print("  ✓ Vue in package.json")

            vue_app = os.path.join(project_dir, "frontend/src/App.vue")
            exists, msg = verify_file(vue_app)
            if not exists:
                all_passed = False
                print("  ✗ App.vue not found")
            else:
                print("  ✓ App.vue found")

        if all_passed:
            results.append((name, True, "All checks passed"))
            print("  ✓ ALL CHECKS PASSED")
        else:
            results.append((name, False, "; ".join(errors)))
            print("  ✗ SOME CHECKS FAILED")

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
