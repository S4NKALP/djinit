"""
User input handling for Django project setup.
Handles collection and processing of user inputs during setup.
"""

import os
import sys
import termios
import tty
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Tuple

from src.scripts.console_ui import UIColors, UIFormatter, console
from src.scripts.name_validator import validate_app_name, validate_project_name


class CICDOption(Enum):
    GITHUB = ("g", "GitHub Actions only")
    GITLAB = ("l", "GitLab CI only")
    BOTH = ("b", "Both (GitHub Actions + GitLab CI)")
    NONE = ("n", "None (skip CI/CD)")

    def __init__(self, key: str, description: str):
        self.key = key
        self.description = description


@dataclass
class ProjectMetadata:
    package_name: str
    use_github_actions: bool = False
    use_gitlab_ci: bool = False
    nested_apps: bool = False
    nested_dir: str | None = None
    use_database_url: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "package_name": self.package_name,
            "use_github_actions": self.use_github_actions,
            "use_gitlab_ci": self.use_gitlab_ci,
            "nested_apps": self.nested_apps,
            "nested_dir": self.nested_dir,
            "use_database_url": self.use_database_url,
        }


@dataclass
class ProjectSetup:
    """Complete project setup configuration."""

    project_dir: str
    project_name: str
    primary_app: str
    app_names: list[str]
    metadata: ProjectMetadata

    def to_tuple(self) -> Tuple[str, str, str, list, dict]:
        """Convert to legacy tuple format for backward compatibility."""
        return (self.project_dir, self.project_name, self.primary_app, self.app_names, self.metadata.to_dict())


class InputCollector:
    """Handles collection of user inputs with validation."""

    MAX_ATTEMPTS = 3

    def __init__(self):
        self.char_reader = CharReader()

    def get_validated_input(
        self, prompt: str, validator: Callable[[str], Tuple[bool, str]], input_type: str, allow_empty: bool = False
    ) -> str:
        attempt = 0

        while attempt < self.MAX_ATTEMPTS:
            try:
                user_input = console.input(f"[{UIColors.HIGHLIGHT}]{prompt}:[/{UIColors.HIGHLIGHT}] ")

                if not user_input.strip():
                    if allow_empty:
                        return ""
                    UIFormatter.print_error(f"{input_type.capitalize()} cannot be empty")
                    attempt += 1
                    self._show_retry_message(attempt)
                    continue

                is_valid, error_msg = validator(user_input)

                if is_valid:
                    return user_input.strip()

                UIFormatter.print_error(error_msg)
                attempt += 1
                self._show_retry_message(attempt)

            except KeyboardInterrupt:
                UIFormatter.print_info("\nSetup cancelled by user.")
                sys.exit(0)
            except Exception as e:
                UIFormatter.print_error(f"Unexpected error: {str(e)}")
                attempt += 1
                self._show_retry_message(attempt)

        UIFormatter.print_error(f"Maximum attempts reached for {input_type}. Exiting.")
        sys.exit(1)

    def _show_retry_message(self, attempt: int) -> None:
        if attempt < self.MAX_ATTEMPTS:
            console.print(f"[{UIColors.MUTED}]Please try again ({attempt}/{self.MAX_ATTEMPTS}).[/{UIColors.MUTED}]")

    def get_app_names(self) -> list[str]:
        try:
            console.print(f"[{UIColors.HIGHLIGHT}]App Names[/{UIColors.HIGHLIGHT}]")
            console.print(
                f"[{UIColors.MUTED}]Enter app names separated by commas (no interactive prompts)[/{UIColors.MUTED}]"
            )
            console.print(f"[{UIColors.MUTED}]Example: users, products, orders[/{UIColors.MUTED}]")

            user_input = console.input(
                f"[{UIColors.HIGHLIGHT}]Enter app names (comma-separated or single):[/{UIColors.HIGHLIGHT}] "
            )

            # Empty input - re-prompt (no interactive flow)
            if not user_input.strip():
                UIFormatter.print_error("At least one app name is required")
                return self.get_app_names()

            # Comma-separated input
            if "," in user_input:
                return self._parse_comma_separated_apps(user_input)

            # Single app (no additional prompts)
            return self._get_apps_starting_with(user_input.strip())

        except KeyboardInterrupt:
            UIFormatter.print_info("\nSetup cancelled by user.")
            sys.exit(0)
        except Exception as e:
            UIFormatter.print_error(f"Unexpected error: {str(e)}")
            return self.get_app_names()  # Retry

    def _parse_comma_separated_apps(self, user_input: str) -> list[str]:
        app_list = [app.strip() for app in user_input.split(",")]
        app_list = [app for app in app_list if app]  # Remove empty strings

        if not app_list:
            UIFormatter.print_error("At least one app name is required")
            return self.get_app_names()

        invalid_apps = []
        for app in app_list:
            is_valid, error_msg = validate_app_name(app)
            if not is_valid:
                invalid_apps.append((app, error_msg))

        if invalid_apps:
            for app, error_msg in invalid_apps:
                UIFormatter.print_error(f"Invalid app name '{app}': {error_msg}")
            return self.get_app_names()

        return app_list

    def _get_apps_starting_with(self, first_app: str) -> list[str]:
        is_valid, error_msg = validate_app_name(first_app)
        if not is_valid:
            UIFormatter.print_error(error_msg)
            return self.get_app_names()

        return [first_app]

    def _get_apps_interactive(self) -> list[str]:
        """Deprecated: interactive flow disabled. Kept for compatibility."""
        UIFormatter.print_warning("Interactive app addition is disabled. Please enter names comma-separated.")
        return self.get_app_names()

    def _prompt_for_additional_apps(self) -> list[str]:
        """Deprecated: interactive flow disabled. Always returns empty list."""
        return []

    def get_cicd_choice(self) -> Tuple[bool, bool]:
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Step 3: CI/CD Pipeline[/{UIColors.INFO}]\n")
        console.print(f"[{UIColors.MUTED}]Choose CI/CD pipeline for your project[/{UIColors.MUTED}]")
        console.print()

        # Show options
        for option in CICDOption:
            console.print(f"  [{UIColors.SUCCESS}]{option.key}[/{UIColors.SUCCESS}]  {option.description}")
        console.print()

        console.print(f"[{UIColors.HIGHLIGHT}]Your choice: [/{UIColors.HIGHLIGHT}]", end="")
        sys.stdout.flush()

        choice = self.char_reader.get_char()
        console.print(choice.upper())

        # Parse choice
        if choice == CICDOption.BOTH.key:
            return True, True
        elif choice == CICDOption.GITHUB.key:
            return True, False
        elif choice == CICDOption.GITLAB.key:
            return False, True
        else:  # Default to none for any unrecognized input
            return False, False

    def get_nested_apps_config(self) -> Tuple[bool, str | None]:
        """Ask whether to create nested Django apps and get directory name if yes."""
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Apps Layout[/{UIColors.INFO}]\n")
        console.print(f"[{UIColors.MUTED}]Do you want to place apps inside a package directory (e.g., 'apps/')?[/{UIColors.MUTED}]")
        console.print(f"[{UIColors.MUTED}]If yes, we'll create that directory as a Python package and generate apps inside it.[/{UIColors.MUTED}]")
        console.print()

        console.print(f"[{UIColors.HIGHLIGHT}]Nested Django apps? (y/N):[/{UIColors.HIGHLIGHT}] ", end="")
        sys.stdout.flush()
        choice = self.char_reader.get_char()
        console.print(choice.upper())

        if choice != "y":
            return False, None

        # Ask for directory name
        dir_name = self.get_validated_input(
            "Enter directory name for apps package (e.g., apps)",
            validate_project_name,
            "apps package name",
        )
        return True, dir_name

    def get_database_config_choice(self) -> bool:
        """Ask user for database configuration preference."""
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Database Configuration[/{UIColors.INFO}]\n")
        console.print(f"[{UIColors.MUTED}]Choose how to configure your database in production:[/{UIColors.MUTED}]")
        console.print()
        console.print(f"  [{UIColors.SUCCESS}]Y[/{UIColors.SUCCESS}]  Use DATABASE_URL (recommended for production)")
        console.print(f"  [{UIColors.SUCCESS}]N[/{UIColors.SUCCESS}]  Use individual database parameters")
        console.print()
        console.print(f"[{UIColors.MUTED}]DATABASE_URL is a single environment variable like:[/{UIColors.MUTED}]")
        console.print(f"[{UIColors.MUTED}]postgres://user:password@host:port/database[/{UIColors.MUTED}]")
        console.print()

        console.print(f"[{UIColors.HIGHLIGHT}]Use DATABASE_URL? (Y/n):[/{UIColors.HIGHLIGHT}] ", end="")
        sys.stdout.flush()
        choice = self.char_reader.get_char()
        console.print(choice.upper())

        # Default to True (use DATABASE_URL) if user presses Enter or Y
        return choice.lower() != "n"


class CharReader:
    """Handles single character input across platforms."""

    @staticmethod
    def get_char() -> str:
        if os.name == "nt":
            return CharReader._get_char_windows()
        return CharReader._get_char_unix()

    @staticmethod
    def _get_char_windows() -> str:
        import msvcrt

        encodings = ["utf-8", "latin1"]

        for encoding in encodings:
            try:
                ch = msvcrt.getch()
                return ch.decode(encoding).lower()
            except (UnicodeDecodeError, AttributeError):
                continue

        # Fallback
        try:
            return msvcrt.getch().lower()
        except:
            return ""

    @staticmethod
    def _get_char_unix() -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_user_input() -> Tuple[str, str, str, list, dict]:
    collector = InputCollector()
    console.print()

    # Section 1: Project Setup
    UIFormatter.print_separator()
    console.print(f"\n[{UIColors.INFO}]Step 1: Project Setup[/{UIColors.INFO}]\n")

    console.print(f"[{UIColors.HIGHLIGHT}]Project Directory[/{UIColors.HIGHLIGHT}]")
    console.print(f"[{UIColors.MUTED}]Where your project files will be created[/{UIColors.MUTED}]")
    project_dir = collector.get_validated_input(
        "Enter project directory name", validate_project_name, "project directory name"
    )
    
    # Check if directory exists and ask for alternative
    while os.path.exists(project_dir):
        UIFormatter.print_error(f"Directory '{project_dir}' already exists.")
        UIFormatter.print_info("Please choose a different project directory name.")
        project_dir = collector.get_validated_input(
            "Enter project directory name", validate_project_name, "project directory name"
        )
    console.print()

    console.print(f"[{UIColors.HIGHLIGHT}]Django Project Name[/{UIColors.HIGHLIGHT}]")
    console.print(f"[{UIColors.MUTED}]Name used in 'django-admin startproject' command[/{UIColors.MUTED}]")
    console.print(f"[{UIColors.MUTED}]Common names: config, core, settings, project_name[/{UIColors.MUTED}]")
    project_name = collector.get_validated_input(
        "Enter Django project name", validate_project_name, "Django project name"
    )
    console.print()

    # Section 2: Django Apps
    console.print()
    UIFormatter.print_separator()
    console.print(f"\n[{UIColors.INFO}]Step 2: Django Apps[/{UIColors.INFO}]\n")
    nested, nested_dir = collector.get_nested_apps_config()
    app_names = collector.get_app_names()
    console.print()

    # Section 3: CI/CD Pipeline
    use_github, use_gitlab = collector.get_cicd_choice()

    # Section 4: Database Configuration
    use_database_url = collector.get_database_config_choice()

    # Create metadata
    metadata = ProjectMetadata(
        package_name=project_dir,
        use_github_actions=use_github,
        use_gitlab_ci=use_gitlab,
        nested_apps=nested,
        nested_dir=nested_dir,
        use_database_url=use_database_url,
    )

    console.print()

    # Return in legacy format for backward compatibility
    return project_dir, project_name, app_names[0], app_names, metadata.to_dict()


def confirm_setup(project_dir: str, project_name: str, app_names: list, metadata: dict) -> bool:
    console.print()
    UIFormatter.print_separator()
    console.print()
    console.print(f"[{UIColors.INFO}]Setup Summary[/{UIColors.INFO}]")
    console.print()

    # Display configuration
    console.print(f"[{UIColors.HIGHLIGHT}]Project Directory:[/{UIColors.HIGHLIGHT}] {project_dir}")
    console.print(f"[{UIColors.HIGHLIGHT}]Django Project:[/{UIColors.HIGHLIGHT}] {project_name}")
    console.print(f"[{UIColors.HIGHLIGHT}]Apps:[/{UIColors.HIGHLIGHT}] {', '.join(app_names)}")
    console.print(f"[{UIColors.HIGHLIGHT}]Package:[/{UIColors.HIGHLIGHT}] {metadata['package_name']}")

    # Show CI/CD choices
    cicd_choices = _get_cicd_display(metadata)
    console.print(f"[{UIColors.HIGHLIGHT}]CI/CD:[/{UIColors.HIGHLIGHT}] {cicd_choices}")

    # Show database configuration
    db_config = "DATABASE_URL" if metadata.get('use_database_url', True) else "Individual parameters"
    console.print(f"[{UIColors.HIGHLIGHT}]Database Config:[/{UIColors.HIGHLIGHT}] {db_config}")

    console.print()
    UIFormatter.print_separator()
    console.print()

    # Get confirmation
    try:
        console.print(f"[{UIColors.WARNING}]Proceed with setup? (y/N):[/{UIColors.WARNING}] ", end="")
        sys.stdout.flush()

        reader = CharReader()
        response = reader.get_char()
        console.print(response.upper())

        return response == "y"

    except KeyboardInterrupt:
        UIFormatter.print_info("\nSetup cancelled by user.")
        return False


def _get_cicd_display(metadata: dict) -> str:
    cicd_choices = []

    if metadata.get("use_github_actions", False):
        cicd_choices.append("GitHub Actions")
    if metadata.get("use_gitlab_ci", False):
        cicd_choices.append("GitLab CI")

    return ", ".join(cicd_choices) if cicd_choices else "None"


get_char = CharReader.get_char
_get_validated_input = InputCollector().get_validated_input
