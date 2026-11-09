import importlib.util
import os
import subprocess
import sys

import pytest

from djinit.creators.setup import SetupCreator

HAS_DJANGO_RUNTIME = all(importlib.util.find_spec(mod) is not None for mod in ("django", "environ", "rest_framework"))

pytestmark = pytest.mark.skipif(
    not HAS_DJANGO_RUNTIME,
    reason="Django runtime dependencies not installed in test environment",
)


@pytest.mark.parametrize(
    "architecture,apps",
    [
        ("modular_monolith", ["accounts", "core"]),
        ("service_layer", ["products"]),
        ("clean_architecture", ["users"]),
        ("multi_tenant", ["projects"]),
    ],
)
def test_django_project_runtime_checks(tmp_path, architecture, apps):
    proj_dir = str(tmp_path / f"test_{architecture}")
    metadata = {
        "package_name": f"test_{architecture}",
        "architecture": architecture,
        "use_database_url": False,
        "database_type": "sqlite3",
        "use_tailwind": False,
        "use_htmx": False,
        "use_vite": False,
    }
    creator = SetupCreator(proj_dir, f"test_{architecture}", "", apps, metadata)
    assert creator.create() is True

    env = {**dict(os.environ), "DJANGO_SETTINGS_MODULE": "config.settings.development"}

    # 1. Django system check
    res_check = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=proj_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_check.returncode == 0, f"check failed for {architecture}:\n{res_check.stderr}"

    # 2. Django makemigrations
    res_make = subprocess.run(
        [sys.executable, "manage.py", "makemigrations"],
        cwd=proj_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_make.returncode == 0, f"makemigrations failed for {architecture}:\n{res_make.stderr}"

    # 3. Dry-run verify migrations
    res_dry = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        cwd=proj_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_dry.returncode == 0, f"makemigrations --check failed for {architecture}:\n{res_dry.stderr}"

    # 4. Migrate database
    res_migrate = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=proj_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_migrate.returncode == 0, f"migrate failed for {architecture}:\n{res_migrate.stderr}"

    # 5. Run tests
    res_test = subprocess.run(
        [sys.executable, "manage.py", "test"],
        cwd=proj_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_test.returncode == 0, f"manage.py test failed for {architecture}:\n{res_test.stderr}"
