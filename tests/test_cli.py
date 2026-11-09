from typer.testing import CliRunner

from djinit.cli import app
from djinit.ui.input import InputCollector
from djinit.utils.common import CommonUtils
from djinit.utils.secretkey import generate_multiple_keys, generate_secret_key
from djinit.utils.validators import validate_app_name, validate_project_name

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


def test_input_collector_frontend_stack_by_architecture():
    collector = InputCollector()

    # fullstack_htmx preset auto-configures htmx + tailwind
    collector.get_alpine_choice = lambda: True
    tailwind, htmx, alpine, vite = collector.get_frontend_stack_choice("fullstack_htmx")
    assert tailwind is True
    assert htmx is True
    assert alpine is True
    assert vite is False

    # lightweight preset defaults to no extra frontend
    tailwind, htmx, alpine, vite = collector.get_frontend_stack_choice("lightweight")
    assert (tailwind, htmx, alpine, vite) == (False, False, False, False)

    # predefined (API-first) defaults to no frontend tools
    tailwind, htmx, alpine, vite = collector.get_frontend_stack_choice("predefined")
    assert (tailwind, htmx, alpine, vite) == (False, False, False, False)

    # standard with selection 'tailwind'
    collector._get_selection = lambda prompt, choices, default="none": "tailwind"
    tailwind, htmx, alpine, vite = collector.get_frontend_stack_choice("standard")
    assert (tailwind, htmx, alpine, vite) == (True, False, False, False)


def test_reserved_names_validation():
    for name in ["django", "test", "admin"]:
        valid, msg = validate_app_name(name)
        assert valid is False
        assert "reserved" in msg.lower() or "conflict" in msg.lower()

        valid_proj, msg_proj = validate_project_name(name)
        assert valid_proj is False
        assert "reserved" in msg_proj.lower() or "conflict" in msg_proj.lower()

    valid_ok, _ = validate_app_name("billing")
    assert valid_ok is True


def test_secret_key_minimum_length_and_count():
    # Clamps to safe minimum length of 16
    key = generate_secret_key(length=5)
    assert len(key) >= 16

    # Clamps to count of at least 1
    keys = generate_multiple_keys(count=0, length=20)
    assert len(keys) == 1
    assert len(keys[0]) == 20


def test_atomic_file_write(tmp_path):
    target_file = str(tmp_path / "deep" / "nested" / "output.txt")
    CommonUtils.create_file_with_content(target_file, "hello atomic world", "Success")

    with open(target_file, encoding="utf-8") as f:
        assert f.read() == "hello atomic world"


def test_cli_help_command_overview():
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0
    assert "djinit - Django Project Initializer CLI" in result.output
    assert "Available Commands & Subcommands" in result.output
    assert "setup" in result.output
    assert "app" in result.output
    assert "secret" in result.output
    assert "template export" in result.output
    assert "template list" in result.output


def test_cli_help_subcommand_details():
    result = runner.invoke(app, ["help", "setup"])
    assert result.exit_code == 0
    assert "setup" in result.output
    assert "--template" in result.output

    res_tpl = runner.invoke(app, ["help", "template"])
    assert res_tpl.exit_code == 0
    assert "export" in res_tpl.output
    assert "list" in res_tpl.output


def test_cli_help_unknown_command():
    result = runner.invoke(app, ["help", "nonexistent"])
    assert result.exit_code != 0
    assert "Unknown command" in result.output


def test_cli_template_help_subcommand():
    result = runner.invoke(app, ["template", "help"])
    assert result.exit_code == 0
    assert "Manage and export custom reusable project templates" in result.output
