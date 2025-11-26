"""
Template engine for djinit.
Handles loading and rendering Jinja2 templates for file generation.
"""

import os
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, Template


class TemplateEngine:
    """Template engine for rendering file templates."""

    def __init__(self, template_dir: str = None):
        """Initialize template engine.

        Args:
            template_dir: Path to templates directory. If None, uses default.
        """
        if template_dir is None:
            # djinit/services/templates.py -> djinit/services -> djinit -> templates
            template_dir = Path(__file__).resolve().parent.parent / "templates"

        if not template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")

        self.template_dir = str(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True
        )

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'gitignore.j2')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template content as string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with the given context.

        Args:
            template_string: Template content as string
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template content as string
        """
        template = Template(template_string, trim_blocks=True, lstrip_blocks=True)
        return template.render(**context)

    def get_template_names(self) -> list[str]:
        """Get list of available template files."""
        if not os.path.exists(self.template_dir):
            return []

        return sorted([file for file in os.listdir(self.template_dir) if file.endswith(".j2")])

    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists.

        Args:
            template_name: Name of the template file

        Returns:
            True if template exists, False otherwise
        """
        template_path = os.path.join(self.template_dir, template_name)
        return os.path.exists(template_path)


template_engine = TemplateEngine()
