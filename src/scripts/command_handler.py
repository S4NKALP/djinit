"""
Command handlers for Django project setup CLI.
Handles different commands like secret key generation and app creation.
"""

import argparse
import sys

from src.scripts.console_ui import UIColors, UIFormatter, console
from src.scripts.name_validator import validate_app_name


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
    app_parser = subparsers.add_parser("app", help="Create a new Django app")
    app_parser.add_argument("app_name", help="Name of the Django app to create")

    return parser.parse_args()


def handle_secret_command(args: argparse.Namespace) -> None:
    from src.scripts.secretkey_generator import display_secret_keys, generate_multiple_keys

    # Generate keys
    keys = generate_multiple_keys(args.count, args.length)

    # Display results
    UIFormatter.print_info("")
    display_secret_keys(keys)

    # Show usage instructions
    from rich.panel import Panel
    from rich.text import Text

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
    from src.scripts.app_generator import AppManager

    # Display welcome message
    UIFormatter.print_info("")
    UIFormatter.print_header("Django App Creation")
    UIFormatter.print_info("")

    # Validate app name
    is_valid, error_msg = validate_app_name(args.app_name)
    if not is_valid:
        UIFormatter.print_error(error_msg)
        sys.exit(1)

    # Create app manager
    app_manager = AppManager(args.app_name)

    # Create the app
    success = app_manager.create_app()

    if not success:
        UIFormatter.print_error(f"Failed to create Django app '{args.app_name}'")
        sys.exit(1)

    UIFormatter.print_success(f"Django app '{args.app_name}' created successfully!")

    # Show next steps
    from rich.panel import Panel
    from rich.text import Text

    instructions = Text()
    instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
    instructions.append("1. The app has been added to INSTALLED_APPS in base.py\n")
    instructions.append("2. Create your models in the app's models.py\n")
    instructions.append("3. Run migrations: python manage.py makemigrations\n")
    instructions.append("4. Apply migrations: python manage.py migrate\n")
    instructions.append("5. Create views, serializers and routes(URLs) for your app\n")

    console.print(Panel(instructions, title="💡 What's Next", border_style="green"))
    UIFormatter.print_info("")
