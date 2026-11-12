import yaml

from djinit.creators.setup import SetupCreator


def _meta(**overrides):
    data = {
        "database_type": "postgresql",
        "use_database_url": True,
        "use_tailwind": False,
        "use_htmx": False,
        "use_alpine": False,
        "use_vite": False,
        "use_github_actions": False,
        "use_gitlab_ci": False,
        "package_name": "backend",
    }
    data.update(overrides)
    return data


def test_dockerfile_and_compose_valid_for_architectures(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # 1. Full-Stack HTMX (uses config.wsgi + tailwind + sqlite3)
    htmx_dir = "proj_htmx"
    assert (
        SetupCreator(
            htmx_dir,
            "proj_htmx",
            "dashboard",
            ["dashboard"],
            _meta(architecture="fullstack_htmx", database_type="sqlite3", use_database_url=False, use_tailwind=True),
        ).create()
        is True
    )
    df_htmx = (tmp_path / htmx_dir / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY . ." in df_htmx
    assert df_htmx.index("COPY . .") < df_htmx.index("tailwind build")
    assert df_htmx.index("tailwind build") < df_htmx.index("collectstatic")
    assert 'CMD ["gunicorn", "config.wsgi:application"' in df_htmx
    assert "USER appuser" in df_htmx

    compose_htmx = yaml.safe_load((tmp_path / htmx_dir / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "web" in compose_htmx["services"]
    assert "db" not in compose_htmx["services"]
    assert "config.wsgi:application" in compose_htmx["services"]["web"]["command"]

    # 2. Modular Monolith + PostgreSQL
    mm_dir = "proj_mm"
    assert (
        SetupCreator(
            mm_dir,
            "proj_mm",
            "accounts",
            ["accounts"],
            _meta(architecture="modular_monolith", database_type="postgresql"),
        ).create()
        is True
    )
    compose_mm = yaml.safe_load((tmp_path / mm_dir / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "db" in compose_mm["services"]
    assert compose_mm["services"]["db"]["healthcheck"]
    assert compose_mm["services"]["web"]["environment"]["DB_HOST"] == "db"
    assert "config.wsgi:application" in compose_mm["services"]["web"]["command"]

    # 3. Unified (uses core.wsgi) + MySQL
    uni_dir = "proj_uni"
    assert (
        SetupCreator(
            uni_dir,
            "proj_uni",
            "users",
            ["users"],
            _meta(unified_structure=True, project_module_name="core", database_type="mysql"),
        ).create()
        is True
    )
    df_uni = (tmp_path / uni_dir / "Dockerfile").read_text(encoding="utf-8")
    assert 'CMD ["gunicorn", "core.wsgi:application"' in df_uni
    compose_uni = yaml.safe_load((tmp_path / uni_dir / "docker-compose.yml").read_text(encoding="utf-8"))
    assert compose_uni["services"]["db"]["image"] == "mysql:8.0"
    assert "core.wsgi:application" in compose_uni["services"]["web"]["command"]
