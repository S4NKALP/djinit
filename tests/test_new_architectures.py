import compileall
from pathlib import Path

from djinit.core.manifest import ManifestManager
from djinit.creators.app import AppCreator
from djinit.creators.setup import SetupCreator


def _assert_valid_python_syntax(root_dir: str):
    """Compile all .py files in the generated project to ensure 100% valid Python syntax."""
    res = compileall.compile_dir(root_dir, quiet=1, force=True)
    assert res, f"Syntax errors found in python files under {root_dir}"


def test_modular_monolith_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "erp_system")
    metadata = {
        "package_name": "erp_system",
        "architecture": "modular_monolith",
        "use_database_url": False,
        "database_type": "sqlite3",
        "use_tailwind": False,
        "use_htmx": False,
        "use_vite": False,
    }
    creator = SetupCreator(proj_dir, "erp_system", "", ["accounts", "core"], metadata)
    assert creator.create() is True

    # Check manifest
    manifest = ManifestManager.load_manifest(proj_dir)
    assert manifest is not None
    assert manifest.project.structure == "modular_monolith"

    # Check config and testing.py
    assert (Path(proj_dir) / "config" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "config" / "settings" / "testing.py").exists()

    # Check common kernel
    assert (Path(proj_dir) / "common" / "db" / "models.py").exists()
    common_models = (Path(proj_dir) / "common" / "db" / "models.py").read_text()
    assert "class OrderedModel" in common_models
    assert "class TimeStampedModel" in common_models
    assert "class SoftDeleteModel" in common_models
    assert "class UUIDModel" in common_models
    assert "class ActivatableModel" in common_models
    assert "class SluggedModel" in common_models
    assert "class BaseModel" in common_models
    assert (Path(proj_dir) / "common" / "permissions" / "base.py").exists()
    assert (Path(proj_dir) / "common" / "middleware" / "request_id.py").exists()

    # Check initial app structure
    accounts_dir = Path(proj_dir) / "apps" / "accounts"
    assert (accounts_dir / "models" / "__init__.py").exists()
    assert (accounts_dir / "services" / "accounts_service.py").exists()
    assert (accounts_dir / "selectors" / "accounts_selector.py").exists()
    assert (accounts_dir / "api" / "urls.py").exists()

    # Now create a new app via AppCreator
    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("inventory")
    assert app_creator.create_app() is True

    inv_dir = Path(proj_dir) / "apps" / "inventory"
    assert (inv_dir / "apps.py").exists()
    assert (inv_dir / "models" / "__init__.py").exists()
    assert (inv_dir / "services" / "inventory_service.py").exists()
    assert (inv_dir / "selectors" / "inventory_selector.py").exists()
    assert (inv_dir / "api" / "serializers.py").exists()

    base_settings = (Path(proj_dir) / "config" / "settings" / "base.py").read_text()
    assert "apps.inventory.apps.InventoryConfig" in base_settings

    # Verify duplicate app is rejected
    assert AppCreator("inventory").create_app() is False

    _assert_valid_python_syntax(proj_dir)


def test_service_layer_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "service_proj")
    metadata = {
        "package_name": "service_proj",
        "architecture": "service_layer",
        "use_database_url": False,
        "database_type": "sqlite3",
    }
    creator = SetupCreator(proj_dir, "service_proj", "", ["products"], metadata)
    assert creator.create() is True

    prod_dir = Path(proj_dir) / "apps" / "products"
    assert (prod_dir / "models.py").exists()
    assert (prod_dir / "services.py").exists()
    assert (prod_dir / "selectors.py").exists()
    assert (prod_dir / "forms.py").exists()
    assert (prod_dir / "api" / "urls.py").exists()

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("orders")
    assert app_creator.create_app() is True

    orders_dir = Path(proj_dir) / "apps" / "orders"
    assert (orders_dir / "services.py").exists()
    assert (orders_dir / "selectors.py").exists()

    base_settings = (Path(proj_dir) / "config" / "settings" / "base.py").read_text()
    assert "apps.orders.apps.OrdersConfig" in base_settings

    _assert_valid_python_syntax(proj_dir)


def test_fullstack_htmx_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "htmx_proj")
    metadata = {
        "package_name": "htmx_proj",
        "architecture": "fullstack_htmx",
        "use_alpine": True,
        "use_tailwind": True,
        "use_htmx": True,
    }
    creator = SetupCreator(proj_dir, "htmx_proj", "", ["dashboard"], metadata)
    assert creator.create() is True

    # Check root templates
    assert (Path(proj_dir) / "templates" / "layouts" / "base.html").exists()
    assert (Path(proj_dir) / "templates" / "components" / "navbar.html").exists()
    assert (Path(proj_dir) / "templates" / "includes" / "messages.html").exists()

    # Check dashboard templates
    dash_dir = Path(proj_dir) / "apps" / "dashboard"
    assert (dash_dir / "templates" / "dashboard" / "index.html").exists()
    assert (dash_dir / "templates" / "dashboard" / "partials" / "item_row.html").exists()

    # Add new HTMX app
    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("tasks")
    assert app_creator.create_app() is True

    tasks_dir = Path(proj_dir) / "apps" / "tasks"
    assert (tasks_dir / "templates" / "tasks" / "index.html").exists()
    assert (tasks_dir / "templates" / "tasks" / "partials" / "item_row.html").exists()
    assert (tasks_dir / "views" / "views.py").exists()

    _assert_valid_python_syntax(proj_dir)


def test_lightweight_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "lite_proj")
    metadata = {
        "package_name": "lite_proj",
        "architecture": "lightweight",
    }
    creator = SetupCreator(proj_dir, "lite_proj", "", [], metadata)
    assert creator.create() is True

    assert (Path(proj_dir) / "lite_proj" / "settings" / "base.py").exists()
    assert (Path(proj_dir) / "templates" / "home.html").exists()

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("notes")
    assert app_creator.create_app() is True
    assert (Path(proj_dir) / "notes" / "apps.py").exists()

    _assert_valid_python_syntax(proj_dir)


def test_ddd_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "ddd_proj")
    metadata = {
        "package_name": "ddd_proj",
        "architecture": "ddd",
    }
    creator = SetupCreator(proj_dir, "ddd_proj", "", ["orders"], metadata)
    assert creator.create() is True

    orders_dir = Path(proj_dir) / "apps" / "orders"
    assert (orders_dir / "domain" / "entities.py").exists()
    assert (orders_dir / "application" / "use_cases.py").exists()
    assert (orders_dir / "infrastructure" / "models.py").exists()
    assert (orders_dir / "infrastructure" / "repositories.py").exists()
    assert (orders_dir / "presentation" / "views.py").exists()

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("billing")
    assert app_creator.create_app() is True

    billing_dir = Path(proj_dir) / "apps" / "billing"
    assert (billing_dir / "domain" / "entities.py").exists()
    assert (billing_dir / "application" / "use_cases.py").exists()
    assert (billing_dir / "infrastructure" / "models.py").exists()

    _assert_valid_python_syntax(proj_dir)


def test_clean_architecture_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "clean_proj")
    metadata = {
        "package_name": "clean_proj",
        "architecture": "clean_architecture",
    }
    creator = SetupCreator(proj_dir, "clean_proj", "", ["users"], metadata)
    assert creator.create() is True

    users_dir = Path(proj_dir) / "apps" / "users"
    assert (users_dir / "domain" / "entities.py").exists()
    assert (users_dir / "use_cases" / "interactors.py").exists()
    assert (users_dir / "interfaces" / "controllers.py").exists()
    assert (users_dir / "infrastructure" / "models.py").exists()

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("reports")
    assert app_creator.create_app() is True

    reports_dir = Path(proj_dir) / "apps" / "reports"
    assert (reports_dir / "use_cases" / "interactors.py").exists()
    assert (reports_dir / "interfaces" / "controllers.py").exists()

    _assert_valid_python_syntax(proj_dir)


def test_multi_tenant_setup_and_app(tmp_path, monkeypatch):
    proj_dir = str(tmp_path / "tenant_proj")
    metadata = {
        "package_name": "tenant_proj",
        "architecture": "multi_tenant",
    }
    creator = SetupCreator(proj_dir, "tenant_proj", "", ["projects"], metadata)
    assert creator.create() is True

    assert (Path(proj_dir) / "tenancy" / "models.py").exists()
    assert (Path(proj_dir) / "tenancy" / "middleware.py").exists()

    base_settings = (Path(proj_dir) / "config" / "settings" / "base.py").read_text()
    assert "tenancy.apps.TenancyConfig" in base_settings
    assert "apps.projects.apps.ProjectsConfig" in base_settings

    monkeypatch.chdir(proj_dir)
    app_creator = AppCreator("invoices")
    assert app_creator.create_app() is True

    invoices_dir = Path(proj_dir) / "apps" / "invoices"
    assert (invoices_dir / "models.py").exists()
    assert (invoices_dir / "services.py").exists()
    assert (invoices_dir / "tests" / "test_isolation.py").exists()

    _assert_valid_python_syntax(proj_dir)
