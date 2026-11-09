from pathlib import Path

from djinit.creators.app import AppCreator
from djinit.creators.setup import SetupCreator


def _create_metadata(structure_type: str, nested: bool = False, nested_dir: str | None = None) -> dict:
    return {
        "package_name": "testpkg",
        "use_github_actions": False,
        "use_gitlab_ci": False,
        "nested_apps": nested,
        "nested_dir": nested_dir,
        "use_database_url": False,
        "database_type": "sqlite3",
        "use_tailwind": False,
        "use_htmx": False,
        "use_vite": False,
        "predefined_structure": structure_type == "predefined",
        "unified_structure": structure_type == "unified",
        "single_structure": structure_type == "single",
        "project_module_name": "config"
        if structure_type == "predefined"
        else "core"
        if structure_type == "unified"
        else "project"
        if structure_type == "single"
        else None,
    }


def test_standard_structure_and_app_creation(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "std_proj")
    metadata = _create_metadata("standard", nested=True, nested_dir="apps")
    creator = SetupCreator(proj_dir, "std_proj", "core", ["core"], metadata)
    assert creator.create() is True

    # Verify key standard files
    assert (Path(proj_dir) / "manage.py").exists()
    assert (Path(proj_dir) / "std_proj" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "apps" / "core" / "apps.py").exists()
    assert (Path(proj_dir) / "shared" / "base.py").exists()

    # Now test creating a new app in standard structure
    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("billing")
    assert app_creator.create_app() is True
    assert (Path(proj_dir) / "apps" / "billing" / "apps.py").exists()
    assert (Path(proj_dir) / "apps" / "billing" / "models.py").exists()

    # Verify settings/base.py contains the new app
    base_settings = (Path(proj_dir) / "std_proj" / "settings" / "base.py").read_text()
    assert "apps.billing.apps.BillingConfig" in base_settings

    # Verify duplicate app creation is rejected
    app_creator_dup = AppCreator("billing")
    assert app_creator_dup.create_app() is False


def test_predefined_structure_and_app_creation(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "predefined_proj")
    metadata = _create_metadata("predefined")
    creator = SetupCreator(proj_dir, "predefined_proj", "users", ["users", "core"], metadata)
    assert creator.create() is True

    assert (Path(proj_dir) / "manage.py").exists()
    assert (Path(proj_dir) / "config" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "apps" / "users" / "apps.py").exists()
    assert (Path(proj_dir) / "api" / "v1" / "urls.py").exists()

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("orders")
    assert app_creator.create_app() is True
    assert (Path(proj_dir) / "apps" / "orders" / "apps.py").exists()

    base_settings = (Path(proj_dir) / "config" / "settings" / "base.py").read_text()
    assert "apps.orders.apps.OrdersConfig" in base_settings


def test_unified_structure(tmp_path):
    proj_dir = str(tmp_path / "unified_proj")
    metadata = _create_metadata("unified")
    creator = SetupCreator(proj_dir, "unified_proj", "", [], metadata)
    assert creator.create() is True

    assert (Path(proj_dir) / "manage.py").exists()
    assert (Path(proj_dir) / "core" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "apps" / "models" / "base.py").exists()
    assert (Path(proj_dir) / "apps" / "api" / "v1" / "urls.py").exists()


def test_single_structure(tmp_path):
    proj_dir = str(tmp_path / "single_proj")
    metadata = _create_metadata("single")
    creator = SetupCreator(proj_dir, "single_proj", "", [], metadata)
    assert creator.create() is True

    assert (Path(proj_dir) / "manage.py").exists()
    assert (Path(proj_dir) / "project" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "project" / "models" / "base.py").exists()
