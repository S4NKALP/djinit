"""
Main script entry point for djinit.
Handles user input validation and orchestrates the setup process.
"""

import os
import subprocess
import sys

from djinit.cli import Cli
from djinit.scripts.command_handler import handle_app_command, handle_secret_command, parse_arguments
from djinit.scripts.console_ui import UIFormatter, console
from djinit.scripts.input_handler import confirm_setup, get_user_input


def clear_screen() -> None:
    try:
        if os.name == "nt":
            subprocess.run("cls", shell=True, check=True)  # Windows
        else:
            subprocess.run("clear", shell=True, check=True)  # Linux/MacOS
    except subprocess.CalledProcessError:
        # If clearing fails, just print some newlines
        console.print("\n" * 50)


def main() -> None:
    # Parse command line arguments
    args = parse_arguments()

    # Handle secret command
    if args.command == "secret":
        handle_secret_command(args)
        return

    # Handle app command
    if args.command == "app":
        handle_app_command(args)
        return

    # Default to setup command
    # Clear screen
    clear_screen()

    # Display welcome screen
    console.print()
    console.print(UIFormatter.create_welcome_panel())
    console.print()

    # Get user input
    project_dir, project_name, primary_app, app_names, metadata = get_user_input()

    # Confirm setup
    if not confirm_setup(project_dir, project_name, app_names, metadata):
        UIFormatter.print_info("Setup cancelled by user.")
        return

    # Run setup
    console.print()
    UIFormatter.print_info("Starting Django project setup...")
    console.print()

    django_cli = Cli(project_dir, project_name, primary_app, app_names, metadata)
    success = django_cli.run_setup()

    # Display completion summary
    UIFormatter.create_summary_panel(project_dir, project_name, app_names, True)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
