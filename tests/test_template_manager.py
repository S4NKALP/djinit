import pytest
from typer.testing import CliRunner

from djinit.cli import app
from djinit.core.template_manager import CustomTemplateManager

runner = CliRunner()


@pytest.fixture
def custom_templates_root(tmp_path, monkeypatch):
    templates_dir = tmp_path / ".djinit" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DJINIT_TEMPLATES_DIR", str(templates_dir))
    return templates_dir


@pytest.fixture
def sample_django_project(tmp_path):
    project_dir = tmp_path / "demo_blog"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Core Django files
    (project_dir / "manage.py").write_text("#!/usr/bin/env python\n# Django demo_blog manage.py")
    (project_dir / ".djinit.toml").write_text('[project]\nname = "demo_blog"\narchitecture = "standard"\n')
    (project_dir / ".env").write_text(
        "SECRET_KEY=raw-secret-key-9999\nDEBUG=True\nDATABASE_URL=postgres://demo_blog:secret@localhost/demo_blog\n"
    )

    inner_dir = project_dir / "demo_blog"
    inner_dir.mkdir()
    (inner_dir / "__init__.py").write_text("")
    (inner_dir / "settings.py").write_text(
        'SECRET_KEY = "raw-secret-key-9999"\nROOT_URLCONF = "demo_blog.urls"\nWSGI_APPLICATION = "demo_blog.wsgi.application"\n'
    )
    (inner_dir / "urls.py").write_text("# URL configuration for demo_blog\n")

    # Files & directories that MUST be ignored during export
    (project_dir / "db.sqlite3").write_bytes(b"SQLite format 3\x00")
    cache_dir = project_dir / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "dummy.cpython-313.pyc").write_bytes(b"pycache")
    venv_dir = project_dir / ".venv" / "bin"
    venv_dir.mkdir(parents=True)
    (venv_dir / "python").write_text("# python binary")

    return project_dir


def test_get_templates_root(tmp_path, monkeypatch):
    custom_dir = tmp_path / "custom_tpl_dir"
    monkeypatch.setenv("DJINIT_TEMPLATES_DIR", str(custom_dir))
    assert CustomTemplateManager.get_templates_root() == custom_dir
    assert custom_dir.is_dir()


def test_export_template_non_django_raises(tmp_path, custom_templates_root):
    non_django = tmp_path / "empty_folder"
    non_django.mkdir()
    with pytest.raises(ValueError, match="not a valid Django project"):
        CustomTemplateManager.export_template(non_django, "my_template")


def test_export_template_invalid_name(sample_django_project, custom_templates_root):
    with pytest.raises(ValueError, match="Invalid template name"):
        CustomTemplateManager.export_template(sample_django_project, "invalid name with spaces!")


def test_export_and_list_template(sample_django_project, custom_templates_root):
    tpl_path = CustomTemplateManager.export_template(
        sample_django_project,
        "starter-blog",
        description="Demo Starter Blog",
    )
    assert tpl_path.is_dir()
    assert (tpl_path / "template_meta.json").is_file()

    # Verify sensitive/unnecessary files were excluded
    assert not (tpl_path / ".venv").exists()
    assert not (tpl_path / "__pycache__").exists()
    assert not (tpl_path / "db.sqlite3").exists()
    assert not (tpl_path / ".env").exists()

    # Verify .env.sample was created and sanitized
    env_sample = tpl_path / ".env.sample"
    assert env_sample.is_file()
    env_sample_text = env_sample.read_text()
    assert "raw-secret-key-9999" not in env_sample_text
    assert "your-secret-key" in env_sample_text

    # Verify project-name mapping in folders
    assert (tpl_path / "__project_name__").is_dir()
    assert not (tpl_path / "demo_blog").exists()

    # Verify parameterization in file contents
    settings_text = (tpl_path / "__project_name__" / "settings.py").read_text()
    assert 'SECRET_KEY = "[[ secret_key ]]"' in settings_text
    assert 'ROOT_URLCONF = "[[ project_name ]].urls"' in settings_text

    # List templates
    templates = CustomTemplateManager.list_templates()
    assert len(templates) == 1
    assert templates[0]["name"] == "starter-blog"
    assert templates[0]["description"] == "Demo Starter Blog"
    assert templates[0]["source_project"] == "demo_blog"


def test_export_template_already_exists_error_and_overwrite(sample_django_project, custom_templates_root):
    CustomTemplateManager.export_template(sample_django_project, "my_tpl")
    with pytest.raises(FileExistsError, match="already exists"):
        CustomTemplateManager.export_template(sample_django_project, "my_tpl", overwrite=False)

    # With overwrite=True, succeeds without error
    overwritten = CustomTemplateManager.export_template(
        sample_django_project, "my_tpl", description="Updated", overwrite=True
    )
    assert overwritten.is_dir()
    meta = CustomTemplateManager.list_templates()[0]
    assert meta["description"] == "Updated"


def test_apply_template(sample_django_project, custom_templates_root, tmp_path):
    CustomTemplateManager.export_template(sample_django_project, "blog_tpl")

    new_project_dir = tmp_path / "acme_portal"
    success = CustomTemplateManager.apply_template("blog_tpl", new_project_dir, "acme_portal")
    assert success is True

    # Check directory remapping
    assert (new_project_dir / "acme_portal").is_dir()
    assert not (new_project_dir / "__project_name__").exists()

    # Check settings rendering
    settings_text = (new_project_dir / "acme_portal" / "settings.py").read_text()
    assert "[[ project_name ]]" not in settings_text
    assert 'ROOT_URLCONF = "acme_portal.urls"' in settings_text
    assert 'WSGI_APPLICATION = "acme_portal.wsgi.application"' in settings_text
    assert 'SECRET_KEY = "[[ secret_key ]]"' not in settings_text
    assert "SECRET_KEY = " in settings_text

    # Check .env creation
    env_file = new_project_dir / ".env"
    assert env_file.is_file()
    env_text = env_file.read_text()
    assert "your-secret-key" not in env_text
    assert "[[ secret_key ]]" not in env_text
    assert "SECRET_KEY=" in env_text


def test_apply_nonexistent_template(custom_templates_root, tmp_path):
    dest = tmp_path / "nowhere"
    success = CustomTemplateManager.apply_template("non_existent", dest, "proj")
    assert success is False


def test_delete_template(sample_django_project, custom_templates_root):
    CustomTemplateManager.export_template(sample_django_project, "tpl_to_delete")
    assert CustomTemplateManager.get_template("tpl_to_delete") is not None

    deleted = CustomTemplateManager.delete_template("tpl_to_delete")
    assert deleted is True
    assert CustomTemplateManager.get_template("tpl_to_delete") is None

    # Deleting again returns False
    assert CustomTemplateManager.delete_template("tpl_to_delete") is False


def test_cli_template_list_empty(custom_templates_root):
    result = runner.invoke(app, ["template", "list"])
    assert result.exit_code == 0
    assert "No custom templates found" in result.output


def test_cli_template_export_and_list(sample_django_project, custom_templates_root):
    # Export via CLI
    result = runner.invoke(
        app,
        [
            "template",
            "export",
            str(sample_django_project),
            "--name",
            "cli-tpl",
            "--description",
            "CLI Exported Template",
        ],
    )
    assert result.exit_code == 0
    assert "Template 'cli-tpl' successfully exported" in result.output

    # List via CLI
    list_res = runner.invoke(app, ["template", "list"])
    assert list_res.exit_code == 0
    assert "cli-tpl" in list_res.output
    assert "CLI Exported Template" in list_res.output


def test_cli_template_export_already_exists_without_force(sample_django_project, custom_templates_root):
    runner.invoke(
        app,
        ["template", "export", str(sample_django_project), "--name", "duplicate-tpl"],
    )
    result = runner.invoke(
        app,
        ["template", "export", str(sample_django_project), "--name", "duplicate-tpl"],
    )
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_cli_template_delete_force(sample_django_project, custom_templates_root):
    CustomTemplateManager.export_template(sample_django_project, "to-remove")
    result = runner.invoke(app, ["template", "delete", "to-remove", "--force"])
    assert result.exit_code == 0
    assert "deleted successfully" in result.output
    assert CustomTemplateManager.get_template("to-remove") is None


def test_cli_template_apply(sample_django_project, custom_templates_root, tmp_path):
    CustomTemplateManager.export_template(sample_django_project, "base-tpl")
    target = tmp_path / "applied_proj"
    result = runner.invoke(
        app,
        [
            "template",
            "apply",
            "base-tpl",
            "--name",
            "applied_proj",
            "--dir",
            str(target),
        ],
    )
    assert result.exit_code == 0
    assert (target / "manage.py").is_file()
    assert (target / "applied_proj" / "settings.py").is_file()


def test_cli_setup_with_template(sample_django_project, custom_templates_root, tmp_path):
    CustomTemplateManager.export_template(sample_django_project, "quick-starter")
    target = tmp_path / "starter_project"
    result = runner.invoke(
        app,
        [
            "setup",
            "--template",
            "quick-starter",
            "--name",
            "starter_project",
            "--dir",
            str(target),
        ],
    )
    assert result.exit_code == 0
    assert (target / "manage.py").is_file()
    assert (target / ".env").is_file()
