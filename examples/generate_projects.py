#!/usr/bin/env python3
"""
Generate real test projects to verify djinit works correctly.
Run from djinit project root: .venv/bin/python examples/generate_projects.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from djinit.creators.setup import SetupCreator


def create_test_project(name, structure, metadata, use_github=False, use_gitlab=False):
    """Create a test project."""
    # Create temp directory
    test_dir = os.path.join("/tmp/djinit_tests", name)
    os.makedirs(test_dir, exist_ok=True)
    original_cwd = os.getcwd()

    try:
        os.chdir(test_dir)

        # Update metadata with defaults
        full_metadata = {
            "package_name": "backend",
            "use_github_actions": use_github,
            "use_gitlab_ci": use_gitlab,
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
            **metadata,
        }

        # Determine structure type
        if structure == "standard":
            full_metadata["project_module_name"] = "config"
            app_names = ["users"]
        elif structure == "predefined":
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

        # Create project
        creator = SetupCreator(
            project_dir=name,
            project_name=name,
            primary_app=app_names[0] if app_names else "",
            app_names=app_names,
            metadata=full_metadata,
        )
        success = creator.create()

        if success:
            print(f"  ✓ Created: {test_dir}")
            return True
        else:
            print(f"  ✗ Failed: {test_dir}")
            return False

    except Exception as e:
        print(f"  ✗ Error creating {name}: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)


def list_project_files(project_dir):
    """List key files in the project."""
    print("\n  Key files:")
    key_files = [
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "package.json",
        "vite.config.js",
        "settings/base.py",
        "manage.py",
    ]

    for root, dirs, files in os.walk(project_dir):
        # Skip hidden and common dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules")]

        for f in files:
            if f in key_files:
                rel_path = os.path.relpath(os.path.join(root, f), project_dir)
                print(f"    - {rel_path}")


def main():
    print("=" * 70)
    print(" DJINIT - GENERATE REAL TEST PROJECTS")
    print("=" * 70)

    # Create test directory
    os.makedirs("/tmp/djinit_tests", exist_ok=True)

    # Define test projects
    test_projects = [
        # Structure: (name, structure, metadata)
        ("test_standard_basic", "standard", {}),
        ("test_standard_docker", "standard", {"use_docker": True}),
        ("test_standard_vite", "standard", {"use_vite": True}),
        (
            "test_standard_all",
            "standard",
            {"use_docker": True, "use_vite": True, "use_tailwind": True, "use_htmx": True},
        ),
        ("test_predefined_basic", "predefined", {}),
        ("test_predefined_docker", "predefined", {"use_docker": True}),
        ("test_unified_basic", "unified", {}),
        ("test_unified_all", "unified", {"use_docker": True, "use_vite": True, "use_tailwind": True}),
        ("test_single_basic", "single", {}),
        ("test_single_docker", "single", {"use_docker": True}),
    ]

    results = []

    for name, structure, metadata in test_projects:
        print(f"\n{'─' * 70}")
        print(f" Creating: {name}")
        print(f" Structure: {structure}")
        print(f" Features: {list(metadata.keys()) if metadata else ['basic']}")

        success = create_test_project(name, structure, metadata)
        results.append((name, success))

        if success:
            list_project_files(f"/tmp/djinit_tests/{name}")

    # Summary
    print("\n" + "=" * 70)
    print(" SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, s in results if s)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\n  🎉 All tests passed!")
    else:
        print("\n  ⚠️  Some tests failed!")

    # Show created directories
    print("\n" + "=" * 70)
    print(" CREATED PROJECTS")
    print("=" * 70)
    for name, _ in results:
        print(f"  /tmp/djinit_tests/{name}")


if __name__ == "__main__":
    main()
