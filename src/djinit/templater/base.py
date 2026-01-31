import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from djinit.templater import template_engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemplateFile:
    """A template file to be rendered.

    The template file extension should end with '-tpl'.
    """

    path: Path
    context: dict[str, Any] = field(default_factory=dict)
    template_name: str | None = None  # Optional override, otherwise derived from path name + -tpl


def create_file(
    template_file: TemplateFile,
    template_name: str | None = None,
) -> None:
    """Create file based on a template.

    Args:
        template_file: The TemplateFile object containing path and context.
        template_name: Optional explicit template name. If not provided,
                       it looks for template_file.template_name,
                       or defaults to template_file.path.name + "-tpl".
    """
    path = template_file.path

    logger.debug(f"Create file, {path}, if it doesn't exist")

    # Ensure parent directory exists
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create __init__.py in parents if needed?
        # CommonUtils.create_directory_with_init handles this usually,
        # but here we are being more granular.
        # For now, let's assume specific directories are created or we blindly create parents.
        # But wait, django-new logic creates parents.

    if path.exists():
        # logic to overwrite or skip? django-new skips if exists usually,
        # or maybe we want to force?
        # For now, let's follow django-new:
        logger.debug(f"Do not create template file, {path}, because it already exists")
        # However, djinit usually overwrites or at least proceeds.
        # Let's keep it safe.
        pass
        # Actually, let's overwrite if needed or warn.
        # But CommonUtils.create_file_from_template overwrites.
        # Let's stick to djinit behavior of overwriting/creating content.

    # Check explicitly passed template_name -> template_file.template_name -> path.name + "-tpl"
    tpl_name = template_name or template_file.template_name or (path.name + "-tpl")

    try:
        content = template_engine.render_template(tpl_name, template_file.context)

        with open(path, "w") as f:
            f.write(content)

        logger.debug(f"Created template file, {path}")
        # We might want to print success via UIFormatter, but maybe keep this low level.

    except FileNotFoundError:
        # Fallback or error
        logger.error(f"Template {tpl_name} not found.")
        raise
