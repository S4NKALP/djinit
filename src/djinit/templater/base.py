import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from djinit.templater import template_engine
from djinit.utils.common import CommonUtils

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
    """Create file based on a template."""
    path = template_file.path
    path.parent.mkdir(parents=True, exist_ok=True)

    tpl_name = template_name or template_file.template_name or (path.name + "-tpl")
    content = template_engine.render_template(tpl_name, template_file.context)
    CommonUtils.write_text_atomic(path, content)
    logger.debug(f"Created template file, {path}")
