import pytest

from djinit.core.manifest import (
    DatabaseSection,
    DeploymentSection,
    FeaturesSection,
    ManifestManager,
    ProjectManifest,
    ProjectSection,
)


def test_manifest_serialization_roundtrip():
    manifest = ProjectManifest(
        project=ProjectSection(
            name="test_erp",
            structure="modular_monolith",
            apps_dir="apps",
            module_name="config",
        ),
        features=FeaturesSection(
            drf=True,
            jwt=True,
            htmx=True,
            tailwind=True,
            alpine=True,
            vite=False,
        ),
        database=DatabaseSection(engine="postgresql", use_database_url=True),
        deployment=DeploymentSection(target="cpanel"),
    )

    toml_str = manifest.to_toml()
    assert "modular_monolith" in toml_str
    assert "postgresql" in toml_str
    assert "cpanel" in toml_str

    loaded = ProjectManifest.from_toml(toml_str)
    assert loaded.project.name == "test_erp"
    assert loaded.project.structure == "modular_monolith"
    assert loaded.features.alpine is True
    assert loaded.database.engine == "postgresql"
    assert loaded.deployment.target == "cpanel"


def test_manifest_aliases():
    manifest = ProjectManifest(project=ProjectSection(name="demo", structure="modular-monolith"))
    assert manifest.project.structure == "modular_monolith"


def test_invalid_structure_raises():
    with pytest.raises(ValueError, match="Unknown structure"):
        ProjectManifest(project=ProjectSection(name="demo", structure="non_existent"))


def test_manifest_save_and_load(tmp_path):
    manifest = ProjectManifest(
        project=ProjectSection(name="myapp", structure="service_layer", apps_dir="apps"),
    )
    ManifestManager.save_manifest(str(tmp_path), manifest)

    assert (tmp_path / ".djinit.toml").is_file()
    loaded = ManifestManager.load_manifest(str(tmp_path))
    assert loaded is not None
    assert loaded.project.name == "myapp"
    assert loaded.project.structure == "service_layer"


def test_load_from_legacy_djinit_json(tmp_path):
    legacy_json = """{
        "project_name": "legacy_proj",
        "structure": {
            "standard": false,
            "predefined": true,
            "unified": false,
            "single": false
        },
        "apps": {
            "nested": true,
            "nested_dir": "apps"
        },
        "settings": {
            "use_database_url": false,
            "database_type": "sqlite3",
            "use_tailwind": true,
            "use_htmx": true,
            "use_vite": false
        }
    }"""
    (tmp_path / ".djinit").write_text(legacy_json)

    loaded = ManifestManager.load_manifest(str(tmp_path))
    assert loaded is not None
    assert loaded.project.name == "legacy_proj"
    assert loaded.project.structure == "predefined"
    assert loaded.project.apps_dir == "apps"
    assert loaded.features.htmx is True
    assert loaded.features.tailwind is True
    assert loaded.database.engine == "sqlite3"
