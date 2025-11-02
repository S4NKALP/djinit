"""
Command handlers for Django project setup CLI.
Handles different commands like secret key generation and app creation.
"""

import argparse
import sys

from rich.panel import Panel
from rich.text import Text

from djinit.scripts.app_generator import AppManager
from djinit.scripts.console_ui import UIColors, UIFormatter, console
from djinit.scripts.name_validator import validate_app_name
from djinit.scripts.secretkey_generator import display_secret_keys, generate_multiple_keys


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Django project setup tool", prog="django-init")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command (default)
    setup_parser = subparsers.add_parser("setup", help="Create a new Django project")
    setup_parser.add_argument("--project", help="Django project name")
    setup_parser.add_argument("--app", help="Django app name")

    # Secret command
    secret_parser = subparsers.add_parser("secret", help="Generate Django secret keys")
    secret_parser.add_argument("--count", type=int, default=3, help="Number of keys to generate")
    secret_parser.add_argument("--length", type=int, default=50, help="Length of each secret key")

    # App command
    app_parser = subparsers.add_parser("app", help="Create one or more Django apps (comma or space separated)")
    app_parser.add_argument(
        "app_name",
        nargs="+",
        help=(
            "App name(s) or comma-separated list. Examples: \n"
            "  djinit app users \n"
            "  djinit app users,products,orders \n"
            "  djinit app users products orders \n"
            "  djinit app users, products, orders"
        ),
    )

    return parser.parse_args()


def handle_secret_command(args: argparse.Namespace) -> None:
    keys = generate_multiple_keys(args.count, args.length)
    UIFormatter.print_info("")
    display_secret_keys(keys)

    instructions = Text()
    instructions.append("📋 Usage Instructions:\n", style=UIColors.ACCENT)
    instructions.append("1. Copy the appropriate secret key for your environment\n")
    instructions.append("2. Add it to your .env file:\n")
    instructions.append("   SECRET_KEY=your_secret_key_here\n", style=UIColors.CODE)
    instructions.append("3. Or set it as an environment variable:\n")
    instructions.append("   export SECRET_KEY=your_secret_key_here\n", style=UIColors.CODE)
    instructions.append("4. Never commit secret keys to version control!\n", style=UIColors.WARNING)

    console.print(Panel(instructions, title="💡 How to Use", border_style="blue"))
    console.print()


def handle_app_command(args: argparse.Namespace) -> None:
    UIFormatter.print_info("")
    UIFormatter.print_header("Django App Creation")
    UIFormatter.print_info("")

    # Parse comma-separated names and validate
    # args.app_name is a list due to nargs="+"; split each token by comma
    tokens = args.app_name if isinstance(args.app_name, list) else [args.app_name]
    pieces = []
    for token in tokens:
        if token is None:
            continue
        for part in str(token).split(","):
            part = part.strip()
            if part:
                pieces.append(part)
    app_names = pieces

    # If no comma, keep single name behavior
    if not app_names:
        UIFormatter.print_error("App name cannot be empty")
        sys.exit(1)

    # Deduplicate while preserving order
    seen = set()
    deduped_names = []
    for name in app_names:
        if name not in seen:
            deduped_names.append(name)
            seen.add(name)

    for name in deduped_names:
        is_valid, error_msg = validate_app_name(name)
        if not is_valid:
            UIFormatter.print_error(f"Invalid app name '{name}': {error_msg}")
            sys.exit(1)

    # Create apps sequentially
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
    instructions.append("3. Run migrations: python manage.py makemigrations\n")
    instructions.append("4. Apply migrations: python manage.py migrate\n")
    instructions.append("5. Create views, serializers and routes(URLs) for your app(s)\n")

    console.print(Panel(instructions, title="💡 What's Next", border_style="green"))
    UIFormatter.print_info("")
