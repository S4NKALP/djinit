import pytest

from djinit.core.parser import InFileLogicParser, SafeExpressionError, safe_eval
from djinit.core.template_manager import CustomTemplateManager
from djinit.templater import template_engine


@pytest.fixture
def custom_templates_root(tmp_path, monkeypatch):
    templates_dir = tmp_path / ".djinit" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DJINIT_TEMPLATES_DIR", str(templates_dir))
    return templates_dir


def test_template_manager_path_traversal_prevention(tmp_path, custom_templates_root):
    # Create an outside sensitive folder
    outside_dir = tmp_path / "sensitive_vault"
    outside_dir.mkdir()
    (outside_dir / "secret.txt").write_text("classified", encoding="utf-8")

    # Relative traversal attempts
    assert CustomTemplateManager.get_template("../../sensitive_vault") is None
    assert CustomTemplateManager.get_template("../") is None
    assert CustomTemplateManager.get_template("..\\windows\\traversal") is None

    # Deletion attempt via path traversal
    deleted = CustomTemplateManager.delete_template("../../sensitive_vault")
    assert deleted is False
    assert (outside_dir / "secret.txt").is_file()

    # Apply attempt with invalid/traversal template name
    target_dir = tmp_path / "new_app"
    applied = CustomTemplateManager.apply_template("../../sensitive_vault", target_dir, "myproj")
    assert applied is False

    # Apply attempt with invalid project name (traversal)
    valid_tpl = custom_templates_root / "valid_tpl"
    valid_tpl.mkdir(parents=True, exist_ok=True)
    (valid_tpl / "manage.py").write_text("# manage.py", encoding="utf-8")

    applied_traversal = CustomTemplateManager.apply_template("valid_tpl", target_dir, "../../malicious")
    assert applied_traversal is False


def test_sanitize_env_content_credentials():
    raw_env = (
        "SECRET_KEY=raw-prod-secret\n"
        "APP_SALT=raw_salt_value_1234\n"
        "SIGNING_CERT=-----BEGIN CERTIFICATE-----\n"
        "WEBHOOK_SIGNATURE=sha256=abcdef123456\n"
        "REDIS_URL=redis://appuser:secretpassword@redis.internal:6379/0\n"
        "CUSTOM_DB_URI=mysql://admin:dbpass@db.internal:3306/prod\n"
        "DATABASE_URL=postgres://demo:pass@localhost:5432/db\n"
        "PROJECT_TITLE=Production blog\n"
    )
    sanitized = CustomTemplateManager._sanitize_env_content(raw_env, "blog")
    assert "raw-prod-secret" not in sanitized
    assert "raw_salt_value_1234" not in sanitized
    assert "BEGIN CERTIFICATE" not in sanitized
    assert "abcdef123456" not in sanitized
    assert "secretpassword" not in sanitized
    assert "dbpass" not in sanitized
    assert "DATABASE_URL=sqlite:///db.sqlite3" in sanitized
    assert "REDIS_URL=redis://127.0.0.1:6379/1" in sanitized
    assert "CUSTOM_DB_URI=mysql://user:password@db.internal:3306/prod" in sanitized


def test_safe_eval_forbidden_attributes():
    with pytest.raises(SafeExpressionError, match="Access to attribute '__class__' is not allowed"):
        safe_eval("x.__class__", {"x": "hello"})

    with pytest.raises(SafeExpressionError, match="Access to attribute 'mro' is not allowed"):
        safe_eval("list.mro()", {"list": list})

    with pytest.raises(SafeExpressionError, match="Access to attribute 'f_globals' is not allowed"):
        safe_eval("f.f_globals", {"f": lambda: None})


def test_safe_eval_dos_protection():
    # Sequence multiplication
    with pytest.raises(SafeExpressionError, match="Sequence multiplication result is too large"):
        safe_eval("'A' * 200_000")

    with pytest.raises(SafeExpressionError, match="Sequence multiplication result is too large"):
        safe_eval("[1, 2] * 100_000")

    # Exponent cap
    with pytest.raises(SafeExpressionError, match="Exponent is too large"):
        safe_eval("2 ** 1001")

    # Comprehension iteration cap
    with pytest.raises(SafeExpressionError, match="Comprehension produced too many items"):
        safe_eval("[x for x in items]", {"items": list(range(15_000))})


def test_production_settings_template_security():
    context = {
        "project_name": "secure_proj",
        "use_database_url": True,
        "database_type": "postgresql",
        "use_tailwind": False,
        "use_vite": False,
    }
    rendered = template_engine.render_template("config/settings/production.py-tpl", context)

    assert "SECURE_SSL_REDIRECT = True" in rendered
    assert "SECURE_HSTS_SECONDS = 31536000" in rendered
    assert "SESSION_COOKIE_SECURE = True" in rendered
    assert "SESSION_COOKIE_HTTPONLY = True" in rendered
    assert "CSRF_COOKIE_SECURE = True" in rendered
    assert "CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])" in rendered
    assert "SECURE_CONTENT_TYPE_NOSNIFF = True" in rendered
    assert "X_FRAME_OPTIONS = 'DENY'" in rendered


def test_urls_template_debug_media_guard():
    context = {
        "url_type": "project",
        "project_name": "secure_proj",
        "include_api": False,
        "include_apps": False,
        "use_tailwind": False,
    }
    rendered = template_engine.render_template("config/urls.py-tpl", context)

    assert "if settings.DEBUG:" in rendered
    assert 'r"^media/(?P<path>.*)$"' in rendered
