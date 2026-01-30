"""
App creation command.
"""

import sys

from rich.panel import Panel
from rich.text import Text

from djinit.core.base import BaseCommand
from djinit.services.app import AppManager
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.utils.validators import validate_app_name


class AppCommand(BaseCommand):
    """Command to create Django apps."""

    def execute(self) -> None:
        UIFormatter.print_info("")
        UIFormatter.print_header("Django App Creation")
        UIFormatter.print_info("")

        raw_tokens = self.args.app_name if isinstance(self.args.app_name, list) else [self.args.app_name]

        # Flatten and clean tokens
        app_names = [part.strip() for token in raw_tokens if token for part in str(token).split(",") if part.strip()]

        if not app_names:
            UIFormatter.print_error("App name cannot be empty")
            sys.exit(1)

        # Deduplicate while preserving order
        deduped_names = list(dict.fromkeys(app_names))

        for name in deduped_names:
            is_valid, error_msg = validate_app_name(name)
            if not is_valid:
                UIFormatter.print_error(f"Invalid app name '{name}': {error_msg}")
                sys.exit(1)

        any_failure = False
        for name in deduped_names:
            app_manager = AppManager(name)
            success = app_manager.create_app()
            if not success:
                UIFormatter.print_error(f"Failed to create Django app '{name}'")
                any_failure = True
                break
            UIFormatter.print_success(f"Django app '{name}' created successfully!")

        if any_failure:
            sys.exit(1)

        instructions = Text()
        instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
        instructions.append("1. The app(s) have been added to INSTALLED_APPS in settings/base.py\n")
        instructions.append("2. Create your models in each app's models.py\n")
        instructions.append("3. Run migrations: just makemigrations\n")
        instructions.append("4. Apply migrations: just migrate\n")
        instructions.append("5. Create views, serializers and routes(URLs) for your app(s)\n")

        console.print(Panel(instructions, title="💡 What's Next", border_style="green"))
        UIFormatter.print_info("")
