"""
Custom Template Manager for djinit.
Allows exporting existing Django projects as reusable custom starter templates
and bootstrapping new projects from saved templates.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from djinit.core.manifest import ManifestManager
from djinit.ui.console import UIFormatter
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
        if env_dir:
            path = Path(env_dir)
        else:
            path = Path.home() / ".djinit" / "templates"
        path.mkdir(parents=True, exist_ok=True)
        return path

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
        if target_dir.exists():
            if not overwrite:
                raise FileExistsError(f"A template named '{clean_name}' already exists at {target_dir}")
            shutil.rmtree(target_dir, ignore_errors=True)

        # Detect source project name via manifest or directory name
        project_name = source.name
        manifest = ManifestManager.load_manifest(str(source))
        if manifest and manifest.project and manifest.project.name:
            project_name = manifest.project.name

        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            for root, dirs, files in os.walk(source):
                # Filter ignored directories in-place
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info")]

                rel_root = Path(root).relative_to(source)

                # Remap directories named after the project to placeholder
                mapped_parts = ["__project_name__" if part == project_name else part for part in rel_root.parts]
                dest_dir = target_dir.joinpath(*mapped_parts)
                dest_dir.mkdir(parents=True, exist_ok=True)

                for file in files:
                    if file in IGNORE_FILES or file.endswith((".pyc", ".pyo", ".sqlite3")):
                        continue

                    src_file = Path(root) / file
                    dest_file = dest_dir / file

                    try:
                        # Try reading as text to parameterize
                        with open(src_file, encoding="utf-8") as f:
                            content = f.read()

                        # Parameterize project name
                        parameterized = content.replace(project_name, "[[ project_name ]]")

                        # Mask hardcoded SECRET_KEY in settings
                        parameterized = re.sub(
                            r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',
                            'SECRET_KEY = "[[ secret_key ]]"',
                            parameterized,
                        )

                        with open(dest_file, "w", encoding="utf-8") as f:
                            f.write(parameterized)
                    except (UnicodeDecodeError, OSError):
                        # Binary file: copy directly
                        shutil.copy2(src_file, dest_file)

            # If .env existed in source but .env.sample does not exist in target, create sanitized .env.sample
            source_env = source / ".env"
            target_env_sample = target_dir / ".env.sample"
            if source_env.is_file() and not target_env_sample.is_file():
                try:
                    env_content = source_env.read_text(encoding="utf-8")
                    # Sanitize secrets in .env.sample
                    env_content = re.sub(
                        r"(SECRET_KEY\s*=\s*).*",
                        r"\1your-secret-key",
                        env_content,
                    )
                    env_content = env_content.replace(project_name, "[[ project_name ]]")
                    target_env_sample.write_text(env_content, encoding="utf-8")
                except OSError:
                    pass

            # Write template metadata
            meta: dict[str, Any] = {
                "name": clean_name,
                "description": description or f"Template exported from {project_name}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_project": project_name,
            }
            with open(target_dir / "template_meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return target_dir
        except Exception:
            # Clean up on failure
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise

    @classmethod
    def list_templates(cls) -> list[dict[str, Any]]:
        """List all available custom templates."""
        root = cls.get_templates_root()
        if not root.is_dir():
            return []

        templates: list[dict[str, Any]] = []
        for child in sorted(root.iterdir()):
            if child.is_dir():
                meta_file = child / "template_meta.json"
                if meta_file.is_file():
                    try:
                        with open(meta_file, encoding="utf-8") as f:
                            meta = json.load(f)
                        templates.append(meta)
                        continue
                    except Exception:
                        pass
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
        """Get template directory path if it exists."""
        target = cls.get_templates_root() / template_name.strip()
        return target if target.is_dir() else None

    @classmethod
    def delete_template(cls, template_name: str) -> bool:
        """Delete a saved custom template."""
        target = cls.get_template(template_name)
        if target and target.is_dir():
            shutil.rmtree(target)
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
            mapped_parts = [project_name if part == "__project_name__" else part for part in rel_root.parts]
            current_dest_dir = dest.joinpath(*mapped_parts)
            current_dest_dir.mkdir(parents=True, exist_ok=True)

            for file in files:
                if file == "template_meta.json":
                    continue

                src_file = Path(root) / file
                dest_file = current_dest_dir / file

                try:
                    with open(src_file, encoding="utf-8") as f:
                        text = f.read()

                    rendered = text.replace("[[ project_name ]]", project_name)
                    rendered = rendered.replace("[[ secret_key ]]", new_secret_key)
                    rendered = rendered.replace("[[ module_name ]]", project_name)

                    with open(dest_file, "w", encoding="utf-8") as f:
                        f.write(rendered)
                except (UnicodeDecodeError, OSError):
                    shutil.copy2(src_file, dest_file)

        # Generate fresh .env if .env.sample exists
        sample_env = dest / ".env.sample"
        env_file = dest / ".env"
        if sample_env.is_file() and not env_file.exists():
            try:
                sample_text = sample_env.read_text(encoding="utf-8")
                sample_text = sample_text.replace("your-secret-key", new_secret_key)
                sample_text = sample_text.replace("[[ secret_key ]]", new_secret_key)
                sample_text = sample_text.replace("[[ project_name ]]", project_name)
                env_file.write_text(sample_text, encoding="utf-8")
            except OSError:
                pass

        UIFormatter.print_success(f"Project '{project_name}' created from template '{template_name}'!")
        return True
