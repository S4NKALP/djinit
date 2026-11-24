"""Read-only checks for a generated Django project."""

import ast
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from djinit.core.manifest import ManifestManager, ProjectManifest
from djinit.core.types import AuthProvider

SETTINGS_MODULE = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)+settings(?:\.[A-Za-z_][A-Za-z0-9_]*)?")
ENV_ASSIGNMENT = re.compile(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)")
COMPOSE_FILES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
DATABASE_ENGINES = {"postgres": "postgresql", "postgresql": "postgresql", "mysql": "mysql", "sqlite": "sqlite3"}


@dataclass(frozen=True)
class Diagnostic:
    status: Literal["OK", "Warning", "Error"]
    check: str
    message: str


def find_project_root(directory: Path) -> Path | None:
    start = directory.resolve()
    for candidate in (start, *start.parents):
        if any((candidate / marker).is_file() for marker in ("manage.py", ".djinit.toml", ".djinit")):
            return candidate
    return None


def read_python(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_bytes())
    except (OSError, SyntaxError, ValueError):
        return None


def settings_path(root: Path, module: str) -> Path | None:
    if not SETTINGS_MODULE.fullmatch(module):
        return None
    path = root.joinpath(*module.split("."))
    for candidate in (path.with_suffix(".py"), path / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def env_call_key(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call) or not node.args:
        return None
    if not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
        return None
    if isinstance(node.func, ast.Name) and node.func.id == "env":
        return node.args[0].value
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "env"
        and node.func.attr == "db"
    ):
        return node.args[0].value
    return None


def database_engine(statements: list[ast.stmt], environment: dict[str, str]) -> str | None:
    """Recognize literal Django backends and the generated django-environ assignments."""
    engine = None
    for stmt in statements:
        if isinstance(stmt, ast.If):
            key = env_call_key(stmt.test)
            if key and environment.get(key):
                engine = database_engine(stmt.body, environment) or engine
        if not isinstance(stmt, ast.Assign):
            continue
        targets = [target.value if isinstance(target, ast.Subscript) else target for target in stmt.targets]
        if not any(isinstance(target, ast.Name) and target.id == "DATABASES" for target in targets):
            continue
        engine = None
        for node in ast.walk(stmt.value):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                prefix = "django.db.backends."
                if node.value.startswith(prefix):
                    engine = node.value.removeprefix(prefix)
            key = env_call_key(node)
            if key and environment.get(key):
                scheme = environment[key].partition(":")[0]
                engine = DATABASE_ENGINES.get(scheme)
    return engine


class ProjectDoctor:
    def __init__(self, root: Path):
        self.root = root
        self.results: list[Diagnostic] = []

    def run(self) -> list[Diagnostic]:
        manifest = self._check_manifest()
        settings_module = self._check_layout(manifest)
        self._check_environment(manifest, settings_module)
        self._check_compose(manifest)
        return self.results

    def _check_manifest(self) -> ProjectManifest | None:
        filename = next((name for name in (".djinit.toml", ".djinit") if (self.root / name).is_file()), None)
        if filename is None:
            self.results.append(Diagnostic("Warning", "Manifest", "No djinit manifest found. Using Django files."))
            return None
        try:
            manifest = ManifestManager.load_manifest(str(self.root))
        except AttributeError:
            manifest = None
        if (
            manifest is None
            or manifest.database.engine not in ("sqlite3", "postgresql", "mysql")
            or not isinstance(manifest.features.auth_providers, list)
        ):
            self.results.append(
                Diagnostic("Error", "Manifest", f"Could not read {filename}. Check its syntax and fields.")
            )
            return None
        self.results.append(Diagnostic("OK", "Manifest", f"Read {filename} ({manifest.project.structure})."))
        return manifest

    def _check_layout(self, manifest: ProjectManifest | None) -> str | None:
        manage = read_python(self.root / "manage.py")
        if manage is None:
            self.results.append(Diagnostic("Error", "Layout", "manage.py is missing, unreadable, or invalid Python."))
            return None
        module = next(
            (
                node.value
                for node in ast.walk(manage)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and SETTINGS_MODULE.fullmatch(node.value)
            ),
            None,
        )
        if module is None:
            self.results.append(
                Diagnostic("Warning", "Layout", "Could not determine the settings module from manage.py.")
            )
            return None

        configured = str(manifest.project.module_name or "") if manifest else ""
        package = module.split(".settings", 1)[0]
        if configured and (self.root / ".djinit.toml").is_file() and configured != package:
            self.results.append(Diagnostic("Error", "Layout", "The manifest and manage.py point to different modules."))
        path = settings_path(self.root, module)
        if path is None or read_python(path) is None:
            self.results.append(
                Diagnostic("Error", "Layout", "The settings selected by manage.py are missing or invalid.")
            )
            return module

        project_dir = self.root.joinpath(*package.split("."))
        if manifest:
            required = [project_dir / name for name in ("urls.py", "wsgi.py", "asgi.py")]
            if path.parent.name == "settings":
                required.extend(path.parent / name for name in ("base.py", "development.py", "production.py"))
            if manifest.features.celery:
                required.append(project_dir / "celery.py")
            if manifest.features.auth_api:
                required.extend(project_dir / "auth_api" / name for name in ("views.py", "serializers.py"))
            missing = [str(file.relative_to(self.root)) for file in required if not file.is_file()]
            if missing:
                self.results.append(Diagnostic("Error", "Layout", f"Missing project files: {', '.join(missing)}."))
                return module
        self.results.append(Diagnostic("OK", "Layout", "manage.py and the expected project files are present."))
        return module

    def _check_environment(self, manifest: ProjectManifest | None, default_module: str | None) -> None:
        path = self.root / ".env"
        values: dict[str, str] = {}
        if path.is_file():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if match := ENV_ASSIGNMENT.fullmatch(line):
                        values[match[1]] = match[2].strip().strip("\"'")
            except (OSError, UnicodeError):
                self.results.append(Diagnostic("Error", "Environment", "Could not read .env."))
                return
        elif (self.root / ".env.sample").is_file():
            self.results.append(Diagnostic("Warning", "Environment", "No .env file. Copy .env.sample for local setup."))
            return

        values.update(os.environ)
        selected_module = values.get("DJANGO_SETTINGS_MODULE", "")
        if selected_module:
            settings = settings_path(self.root, selected_module)
            if settings is None or read_python(settings) is None:
                self.results.append(
                    Diagnostic("Error", "Environment", "DJANGO_SETTINGS_MODULE points to missing or invalid settings.")
                )
                return
        module = selected_module or default_module or ""
        if module.endswith(".settings.production"):
            if values.get("SECRET_KEY", "") in {"", "your-secret-key"}:
                self.results.append(
                    Diagnostic("Error", "Environment", "Production settings require a configured SECRET_KEY.")
                )
                return
            if manifest and manifest.database.use_database_url and not values.get("DATABASE_URL"):
                self.results.append(Diagnostic("Error", "Environment", "Production settings require DATABASE_URL."))
                return
            if manifest and not manifest.database.use_database_url and manifest.database.engine != "sqlite3":
                missing = [key for key in ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST") if key not in values]
                if missing:
                    message = f"Production database variables are missing: {', '.join(missing)}."
                    self.results.append(Diagnostic("Error", "Environment", message))
                    return
        if manifest:
            missing = [
                key
                for provider in AuthProvider
                if provider.value in manifest.features.auth_providers
                for suffix in ("ID", "SECRET")
                if not values.get(key := f"{provider.name}_CLIENT_{suffix}")
            ]
            if missing:
                message = f"Missing OAuth environment variables: {', '.join(missing)}. Credentials can also be set in Django admin."
                self.results.append(Diagnostic("Warning", "Environment", message))
                return
        if path.is_file():
            self.results.append(Diagnostic("OK", "Environment", "Local .env settings passed the checks."))

    def _check_compose(self, manifest: ProjectManifest | None) -> None:
        filename = next((name for name in COMPOSE_FILES if (self.root / name).is_file()), None)
        if filename is None:
            self.results.append(Diagnostic("Warning", "Compose", "No Compose file found."))
            return
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", filename, "config", "--format", "json"],
                cwd=self.root,
                capture_output=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            self.results.append(
                Diagnostic("Warning", "Compose", "Docker is unavailable. Compose validation was skipped.")
            )
            return
        except (OSError, subprocess.TimeoutExpired):
            self.results.append(Diagnostic("Warning", "Compose", "Could not run Compose validation."))
            return
        if result.returncode:
            stderr = result.stderr.lower()
            if b"unknown command" in stderr or b"is not a docker command" in stderr:
                self.results.append(Diagnostic("Warning", "Compose", "The Docker Compose plugin is unavailable."))
            else:
                self.results.append(
                    Diagnostic("Error", "Compose", "Run docker compose config --quiet to check this file.")
                )
            return
        try:
            services = json.loads(result.stdout)["services"]
        except (ValueError, KeyError, TypeError):
            self.results.append(Diagnostic("Error", "Compose", "Could not read the rendered services."))
            return
        self.results.append(Diagnostic("OK", "Compose", f"{filename} is valid."))
        if manifest:
            expected = set()
            if manifest.features.celery:
                expected.update(("worker", "redis"))
            if manifest.features.celery_beat:
                expected.add("beat")
            if manifest.features.redis_cache:
                expected.add("redis")
            missing = sorted(expected - services.keys())
            if missing:
                self.results.append(Diagnostic("Error", "Compose", f"Missing preset services: {', '.join(missing)}."))
        self._check_compose_database(services, manifest)

    def _check_compose_database(self, services: dict, manifest: ProjectManifest | None) -> None:
        web = services.get("web")
        if not web:
            return
        environment = web.get("environment") or {}
        path = settings_path(self.root, environment.get("DJANGO_SETTINGS_MODULE") or "")
        if path is None or (tree := read_python(path)) is None:
            self.results.append(Diagnostic("Warning", "Database", "Could not inspect the settings used by Compose."))
            return
        image = services.get("db", {}).get("image", "").split("/")[-1].partition("@")[0].partition(":")[0]
        service_engine = DATABASE_ENGINES.get(image)
        manifest_engine = manifest.database.engine if manifest else None
        if service_engine and manifest_engine and service_engine != manifest_engine:
            self.results.append(
                Diagnostic("Error", "Database", "The Compose database service disagrees with the manifest.")
            )
            return
        expected = service_engine or manifest_engine
        engine = database_engine(tree.body, environment)
        if engine is None or expected is None:
            self.results.append(
                Diagnostic("Warning", "Database", "Could not infer the Compose database from settings.")
            )
        elif expected and engine != expected:
            labels = {"sqlite3": "SQLite", "postgresql": "PostgreSQL", "mysql": "MySQL"}
            message = f"Compose expects {labels.get(expected, 'the selected database')} but Django settings use {labels.get(engine, 'a different backend')}."
            self.results.append(Diagnostic("Error", "Database", message))
        else:
            self.results.append(
                Diagnostic("OK", "Database", "Django settings match the Compose database configuration.")
            )
