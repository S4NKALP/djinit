"""
Custom Template Manager for djinit.
Allows exporting existing Django projects as reusable custom starter templates
and bootstrapping new projects from saved templates.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from djinit.core.manifest import ManifestManager
from djinit.ui.console import UIFormatter
from djinit.utils.common import CommonUtils
from djinit.utils.secretkey import generate_secret_key

IGNORE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        "htmlcov",
        "dist",
        "build",
        "media",
    }
)

IGNORE_FILES = frozenset(
    {
        ".coverage",
        "db.sqlite3",
        ".env",
        ".env.local",
        ".DS_Store",
        "Thumbs.db",
    }
)

NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


class CustomTemplateManager:
    """Manages custom project template export, storage, and instantiation."""

    @classmethod
    def get_templates_root(cls) -> Path:
        """Get the base directory for stored custom templates."""
        env_dir = os.environ.get("DJINIT_TEMPLATES_DIR")
        path = Path(env_dir) if env_dir else Path.home() / ".djinit" / "templates"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _parameterize_content(content: str, project_name: str) -> str:
        """Replace project name with placeholder using word boundaries to avoid partial corruption."""
        pattern = re.compile(r"\b" + re.escape(project_name) + r"\b")
        parameterized = pattern.sub("[[ project_name ]]", content)
        # Mask hardcoded SECRET_KEY in Django settings
        return re.sub(
            r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',
            'SECRET_KEY = "[[ secret_key ]]"',
            parameterized,
        )

    @staticmethod
    def _sanitize_env_content(env_content: str, project_name: str) -> str:
        """Sanitize environment variables for safe export, preventing secret leakage."""
        sensitive_keywords = (
            "SECRET",
            "PASSWORD",
            "KEY",
            "TOKEN",
            "CREDENTIAL",
            "AUTH",
            "PASS",
            "SALT",
            "CERT",
            "SIGNATURE",
        )
        lines = []
        for line in env_content.splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or "=" not in line:
                lines.append(line)
                continue
            key, _, val = line.partition("=")
            key_name = key.strip()
            key_upper = key_name.upper()

            if "SECRET_KEY" in key_upper:
                lines.append(f"{key_name}=your-secret-key")
            elif any(s in key_upper for s in sensitive_keywords):
                lines.append(f"{key_name}=your-{key_name.lower().replace('_', '-')}")
            elif "DATABASE_URL" in key_upper or "DB_URL" in key_upper:
                lines.append(f"{key_name}=sqlite:///db.sqlite3")
            elif any(k in key_upper for k in ("REDIS_URL", "CACHE_URL", "BROKER_URL")):
                lines.append(f"{key_name}=redis://127.0.0.1:6379/1")
            elif "://" in val and "@" in val:
                sanitized_val = re.sub(r"://([^:]+):([^@]+)@", "://user:password@", val)
                lines.append(f"{key_name}={sanitized_val}")
            else:
                pattern = re.compile(r"\b" + re.escape(project_name) + r"\b")
                lines.append(f"{key_name}={pattern.sub('[[ project_name ]]', val)}")
        return "\n".join(lines) + "\n"

    @classmethod
    def export_template(
        cls,
        source_dir: str | Path,
        template_name: str,
        description: str = "",
        overwrite: bool = False,
    ) -> Path:
        """Export an existing Django project directory as a reusable custom template."""
        source = Path(source_dir).resolve()
        if not (source / "manage.py").is_file():
            raise ValueError(f"'{source}' is not a valid Django project (missing manage.py).")

        clean_name = template_name.strip()
        if not clean_name or not NAME_REGEX.match(clean_name):
            raise ValueError(
                f"Invalid template name '{template_name}'. Name must contain only letters, numbers, underscores, and hyphens."
            )

        target_dir = cls.get_templates_root() / clean_name
        if target_dir.exists() and not overwrite:
            raise FileExistsError(f"A template named '{clean_name}' already exists at {target_dir}")

        # Detect source project name via manifest or directory name
        project_name = source.name
        manifest = ManifestManager.load_manifest(str(source))
        if manifest and manifest.project and manifest.project.name:
            project_name = manifest.project.name

        # Use an isolated staging directory to avoid partial writes / race conditions
        staging_dir = target_dir.parent / f".tmp_{clean_name}_{secrets.token_hex(4)}"
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            for root, dirs, files in os.walk(source):
                # Filter ignored directories in-place
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info")]

                rel_root = Path(root).relative_to(source)

                # Remap directories named after the project to placeholder
                mapped_parts = ["__project_name__" if part == project_name else part for part in rel_root.parts]
                dest_dir = staging_dir.joinpath(*mapped_parts).resolve()
                if not dest_dir.is_relative_to(staging_dir.resolve()):
                    continue
                dest_dir.mkdir(parents=True, exist_ok=True)

                for file in files:
                    if file in IGNORE_FILES or file.endswith((".pyc", ".pyo", ".sqlite3")):
                        continue

                    src_file = Path(root) / file
                    dest_file = (dest_dir / file).resolve()
                    if not dest_file.is_relative_to(staging_dir.resolve()):
                        continue

                    try:
                        content = src_file.read_text(encoding="utf-8")
                        dest_file.write_text(cls._parameterize_content(content, project_name), encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        # Binary file: copy directly
                        shutil.copy2(src_file, dest_file)

            # If .env existed in source but .env.sample does not exist in target, create sanitized .env.sample
            source_env = source / ".env"
            target_env_sample = staging_dir / ".env.sample"
            if source_env.is_file() and not target_env_sample.is_file():
                with suppress(OSError):
                    env_content = source_env.read_text(encoding="utf-8")
                    target_env_sample.write_text(cls._sanitize_env_content(env_content, project_name), encoding="utf-8")

            # Write template metadata
            meta: dict[str, Any] = {
                "name": clean_name,
                "description": description or f"Template exported from {project_name}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_project": project_name,
            }
            meta_json = json.dumps(meta, indent=2)
            CommonUtils.write_text_atomic(staging_dir / "template_meta.json", meta_json)

            # Atomic swap to target_dir
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            staging_dir.replace(target_dir)

            return target_dir
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

    @classmethod
    def list_templates(cls) -> list[dict[str, Any]]:
        """List all available custom templates."""
        root = cls.get_templates_root()
        if not root.is_dir():
            return []

        templates: list[dict[str, Any]] = []
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                meta_file = child / "template_meta.json"
                if meta_file.is_file():
                    with suppress(json.JSONDecodeError, OSError):
                        templates.append(json.loads(meta_file.read_text(encoding="utf-8")))
                        continue
                templates.append(
                    {
                        "name": child.name,
                        "description": "Custom template",
                        "created_at": datetime.fromtimestamp(child.stat().st_ctime, timezone.utc).isoformat(),
                        "source_project": "unknown",
                    }
                )
        return templates

    @classmethod
    def get_template(cls, template_name: str) -> Path | None:
        """Get template directory path if it exists, safely preventing path traversal."""
        clean_name = template_name.strip()
        if not clean_name or not NAME_REGEX.match(clean_name):
            return None
        root = cls.get_templates_root().resolve()
        target = (root / clean_name).resolve()
        if not target.is_relative_to(root):
            return None
        return target if target.is_dir() else None

    @classmethod
    def delete_template(cls, template_name: str) -> bool:
        """Delete a saved custom template."""
        target = cls.get_template(template_name)
        if target and target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            return True
        return False

    @classmethod
    def apply_template(
        cls,
        template_name: str,
        target_dir: str | Path,
        project_name: str,
    ) -> bool:
        """Instantiate a new project from a custom template."""
        clean_proj = project_name.strip()
        if not clean_proj or not NAME_REGEX.match(clean_proj):
            UIFormatter.print_error(
                f"Invalid project name '{project_name}'. Name must contain only letters, numbers, underscores, and hyphens."
            )
            return False

        template_path = cls.get_template(template_name)
        if not template_path:
            UIFormatter.print_error(f"Template '{template_name}' not found.")
            return False

        dest = Path(target_dir).resolve()
        dest.mkdir(parents=True, exist_ok=True)

        new_secret_key = generate_secret_key(50)

        for root, _dirs, files in os.walk(template_path):
            rel_root = Path(root).relative_to(template_path)

            # Map __project_name__ placeholder back to actual project name
            mapped_parts = [clean_proj if part == "__project_name__" else part for part in rel_root.parts]
            current_dest_dir = dest.joinpath(*mapped_parts).resolve()
            if not current_dest_dir.is_relative_to(dest):
                continue
            current_dest_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file == "template_meta.json":
                    continue

                src_file = Path(root) / file
                dest_file_name = file.replace("__project_name__", clean_proj)
                dest_file = (current_dest_dir / dest_file_name).resolve()
                if not dest_file.is_relative_to(dest):
                    continue

                try:
                    text = src_file.read_text(encoding="utf-8")
                    rendered = (
                        text.replace("[[ project_name ]]", clean_proj)
                        .replace("[[ secret_key ]]", new_secret_key)
                        .replace("[[ module_name ]]", clean_proj)
                    )
                    dest_file.write_text(rendered, encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    shutil.copy2(src_file, dest_file)

        # Generate fresh .env if .env.sample exists
        sample_env = dest / ".env.sample"
        env_file = dest / ".env"
        if sample_env.is_file() and not env_file.exists():
            with suppress(OSError):
                sample_text = (
                    sample_env.read_text(encoding="utf-8")
                    .replace("your-secret-key", new_secret_key)
                    .replace("[[ secret_key ]]", new_secret_key)
                    .replace("[[ project_name ]]", clean_proj)
                )
                env_file.write_text(sample_text, encoding="utf-8")

        UIFormatter.print_success(f"Project '{clean_proj}' created from template '{template_name}'!")
        return True
