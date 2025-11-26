"""
Main script entry point for djinit.
Handles user input validation and orchestrates the setup process.
"""

import os
import subprocess
import sys

from djinit.cli import Cli
from djinit.commands.handler import handle_app_command, handle_secret_command, parse_arguments
from djinit.ui.console import UIFormatter, console
from djinit.ui.input import confirm_setup, get_user_input


def clear_screen() -> None:
    try:
        if os.name == "nt":
            subprocess.run("cls", shell=True, check=True)
        else:
            subprocess.run("clear", shell=True, check=True)
    except subprocess.CalledProcessError:
        console.print("\n" * 50)


def main() -> None:
    args = parse_arguments()

    if args.command == "secret":
        handle_secret_command(args)
        return

    if args.command == "app":
        handle_app_command(args)
        return

    clear_screen()

    console.print()
    console.print(UIFormatter.create_welcome_panel())
    console.print()

    project_dir, project_name, primary_app, app_names, metadata = get_user_input()

    if not confirm_setup(project_dir, project_name, app_names, metadata):
        UIFormatter.print_info("Setup cancelled by user.")
        return

    console.print()
    UIFormatter.print_info("Starting Django project setup...")
    console.print()

    django_cli = Cli(project_dir, project_name, primary_app, app_names, metadata)
    success = django_cli.run_setup()

    UIFormatter.create_summary_panel(project_dir, project_name, app_names, True, metadata=metadata)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
