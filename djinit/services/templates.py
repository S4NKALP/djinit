"""
Template engine for djinit.
Handles loading and rendering Jinja2 templates for file generation.
"""

import os
from pathlib import Path
from typing import Any, Dict

from djinit.core.parser import InFileLogicParser


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
        self.parser = InFileLogicParser()

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'gitignore.py-tpl')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template content as string
        """
        template_path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r") as f:
            template_text = f.read()

        return self.parser.render(template_text, context)

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with the given context.

        Args:
            template_string: Template content as string
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template content as string
        """
        return self.parser.render(template_string, context)

    def get_template_names(self) -> list[str]:
        """Get list of available template files."""
        if not os.path.exists(self.template_dir):
            return []

        templates = []
        for root, _, files in os.walk(self.template_dir):
            for file in files:
                if file.endswith("-tpl"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.template_dir)
                    templates.append(rel_path)
        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists.

        Args:
            template_name: Name of the template file
        """
        template_path = os.path.join(self.template_dir, template_name)
        return os.path.exists(template_path)


template_engine = TemplateEngine()
