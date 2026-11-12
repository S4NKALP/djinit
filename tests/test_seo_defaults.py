from pathlib import Path

from djinit.creators.setup import SetupCreator


def _base_metadata(**overrides):
    meta = {
        "database_type": "sqlite3",
        "use_database_url": False,
        "use_tailwind": False,
        "use_htmx": False,
        "use_alpine": False,
        "use_vite": False,
        "use_github_actions": False,
        "use_gitlab_ci": False,
        "package_name": "backend",
    }
    meta.update(overrides)
    return meta


def test_standard_structure_includes_default_seo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = "seo_std_proj"
    orchestrator = SetupCreator(proj_dir, "seo_std_proj", "core", ["core"], _base_metadata())
    assert orchestrator.create() is True

    root = tmp_path / proj_dir
    assert (root / "seo_std_proj" / "sitemaps.py").is_file()
    assert (root / "seo_std_proj" / "context_processors.py").is_file()

    base_settings = (root / "seo_std_proj" / "settings" / "base.py").read_text(encoding="utf-8")
    assert '"django.contrib.sitemaps"' in base_settings
    assert '"seo_std_proj.context_processors.seo_context"' in base_settings
    assert 'SITE_NAME = env("SITE_NAME"' in base_settings
    assert "SITE_DESCRIPTION = env(" in base_settings

    urls_py = (root / "seo_std_proj" / "urls.py").read_text(encoding="utf-8")
    assert "sitemap.xml" in urls_py
    assert "robots.txt" in urls_py
    assert "StaticViewSitemap" in urls_py


def test_fullstack_htmx_includes_seo_meta_partial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = "seo_htmx_proj"
    meta = _base_metadata(architecture="fullstack_htmx", use_htmx=True, use_tailwind=True)
    orchestrator = SetupCreator(proj_dir, "seo_htmx_proj", "dashboard", ["dashboard"], meta)
    assert orchestrator.create() is True

    root = Path(tmp_path / proj_dir)
    assert (root / "config" / "sitemaps.py").is_file()
    assert (root / "config" / "context_processors.py").is_file()

    seo_meta = root / "templates" / "includes" / "seo_meta.html"
    assert seo_meta.is_file()
    seo_meta_text = seo_meta.read_text(encoding="utf-8")
    assert "og:title" in seo_meta_text
    assert "twitter:card" in seo_meta_text
    assert 'rel="canonical"' in seo_meta_text

    base_html = (root / "templates" / "layouts" / "base.html").read_text(encoding="utf-8")
    assert 'includes/seo_meta.html' in base_html


def test_lightweight_includes_seo_in_home_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = "seo_light_proj"
    meta = _base_metadata(architecture="lightweight", single_structure=True)
    orchestrator = SetupCreator(proj_dir, "seo_light_proj", "core", [], meta)
    assert orchestrator.create() is True

    root = tmp_path / proj_dir
    assert (root / "seo_light_proj" / "sitemaps.py").is_file()
    assert (root / "seo_light_proj" / "context_processors.py").is_file()

    home_html = (root / "templates" / "home.html").read_text(encoding="utf-8")
    assert "seo_description" in home_html
    assert "seo_canonical_url" in home_html
    assert "og:title" in home_html
