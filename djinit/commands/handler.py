"""
Command handlers for Django project setup CLI.
Handles different commands like secret key generation and app creation.
"""

import argparse


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Django project setup tool", prog="django-init")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    setup_parser = subparsers.add_parser("setup", help="Create a new Django project")
    setup_parser.add_argument("--project", help="Django project name")
    setup_parser.add_argument("--app", help="Django app name")

    secret_parser = subparsers.add_parser("secret", help="Generate Django secret keys")
    secret_parser.add_argument("--count", type=int, default=3, help="Number of keys to generate")
    secret_parser.add_argument("--length", type=int, default=50, help="Length of each secret key")

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
    from djinit.commands.secret import SecretCommand

    command = SecretCommand(args)
    command.execute()


def handle_app_command(args: argparse.Namespace) -> None:
    from djinit.commands.app import AppCommand

    command = AppCommand(args)
    command.execute()
