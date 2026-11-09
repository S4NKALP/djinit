from typer.testing import CliRunner

from djinit.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Django Project Initializer" in result.output or "djinit" in result.output
    assert "secret" in result.output
    assert "app" in result.output
    assert "setup" in result.output


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "djinit" in result.output


def test_cli_secret():
    result = runner.invoke(app, ["secret", "--count", "2", "--length", "32"])
    assert result.exit_code == 0
    assert "Django Secret Keys" in result.output
    assert "SECRET_KEY=" in result.output


def test_cli_app_outside_django_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["app", "testapp"])
    assert result.exit_code != 0
    assert "Not in a Django project directory" in result.output


def test_cli_app_invalid_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Even if manage.py exists, invalid app name should be rejected
    (tmp_path / "manage.py").write_text("")
    result = runner.invoke(app, ["app", "123-invalid-name!"])
    assert result.exit_code != 0
    assert "Invalid app name" in result.output
