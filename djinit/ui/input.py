"""
User input handling for Django project setup.
Handles collection and processing of user inputs during setup.
"""

import os
import sys
import termios
import tty
from enum import Enum
from typing import Callable, Tuple

from djinit.core.types import ProjectMetadata
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.utils.common import get_package_name
from djinit.utils.validators import validate_app_name, validate_project_name


class CICDOption(Enum):
    GITHUB = ("g", "GitHub Actions only")
    GITLAB = ("l", "GitLab CI only")
    BOTH = ("b", "Both (GitHub Actions + GitLab CI)")
    NONE = ("n", "None (skip CI/CD)")

    def __init__(self, key: str, description: str):
        self.key = key
        self.description = description


class InputCollector:
    MAX_ATTEMPTS = 3

    def __init__(self):
        pass

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

    def _show_retry_message(self, attempt: int, max_attempts: int = None) -> None:
        max_attempts = max_attempts or self.MAX_ATTEMPTS
        if attempt < max_attempts:
            console.print(f"[{UIColors.MUTED}]Please try again ({attempt}/{max_attempts}).[/{UIColors.MUTED}]")

    def get_app_names(self) -> list[str]:
        console.print(
            f"[{UIColors.MUTED}]Enter app names separated by commas(e.g. users, products, orders)[/{UIColors.MUTED}]"
        )

        user_input = console.input(
            f"[{UIColors.HIGHLIGHT}]Enter app names (comma-separated or single):[/{UIColors.HIGHLIGHT}] "
        )

        if not user_input.strip():
            UIFormatter.print_error("At least one app name is required")
            return self.get_app_names()

        if "," in user_input:
            return self._parse_comma_separated_apps(user_input)

        return self._get_apps_starting_with(user_input.strip())

    def _parse_comma_separated_apps(self, user_input: str) -> list[str]:
        app_list = [app.strip() for app in user_input.split(",") if app.strip()]

        if not app_list:
            UIFormatter.print_error("At least one app name is required")
            return self.get_app_names()

        return self._validate_app_list(app_list)

    def _get_apps_starting_with(self, first_app: str) -> list[str]:
        return self._validate_app_list([first_app])

    def _validate_app_list(self, app_list: list[str]) -> list[str]:
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

    def _get_project_directory(self) -> str | None:
        attempt = 0

        while attempt < self.MAX_ATTEMPTS:
            try:
                user_input = console.input(
                    f"[{UIColors.HIGHLIGHT}]Enter project directory name:[/{UIColors.HIGHLIGHT}] "
                ).strip()

                if not user_input or user_input == ".":
                    UIFormatter.print_info(f"Creating project in current directory: {os.getcwd()}")
                    return "."

                is_valid, error_msg = validate_project_name(user_input)
                if not is_valid:
                    UIFormatter.print_error(error_msg)
                    attempt += 1
                    self._show_retry_message(attempt)
                    continue

                if os.path.exists(user_input):
                    UIFormatter.print_error(f"Directory '{user_input}' already exists.")
                    UIFormatter.print_info(
                        "Please choose a different project directory name (or press Enter for current directory)."
                    )
                    attempt += 1
                    self._show_retry_message(attempt)
                    continue

                return user_input

            except KeyboardInterrupt:
                UIFormatter.print_info("\nSetup cancelled by user.")
                sys.exit(0)

        return None

    def get_cicd_choice(self) -> Tuple[bool, bool]:
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]CI/CD Pipeline[/{UIColors.INFO}]\n")
        console.print()

        for option in CICDOption:
            console.print(f"  [{UIColors.SUCCESS}]{option.key}[/{UIColors.SUCCESS}]  {option.description}")
        console.print()

        valid_keys = [option.key for option in CICDOption]

        choice = CharReader.get_cicd_choice(
            f"[{UIColors.HIGHLIGHT}]Your choice: [/{UIColors.HIGHLIGHT}]",
            valid_keys=valid_keys,
            default=CICDOption.NONE.key,
        )

        choice_map = {
            CICDOption.BOTH.key: (True, True),
            CICDOption.GITHUB.key: (True, False),
            CICDOption.GITLAB.key: (False, True),
        }
        return choice_map.get(choice, (False, False))

    def get_nested_apps_config(self) -> Tuple[bool, str | None]:
        UIFormatter.print_separator()
        console.print(
            f"[{UIColors.MUTED}]Do you want to place apps inside a package directory (e.g. 'src/')?[/{UIColors.MUTED}]"
        )
        console.print()

        choice = CharReader.get_yes_no(f"[{UIColors.HIGHLIGHT}]Nested Django apps? (y/N):[/{UIColors.HIGHLIGHT}]")

        if choice != "y":
            return False, None

        dir_name = self.get_validated_input(
            "Enter directory name for apps package (e.g. src)",
            validate_project_name,
            "apps package name",
        )
        return True, dir_name

    def get_database_config_choice(self) -> bool:
        UIFormatter.print_separator()
        console.print()
        console.print(f"  [{UIColors.SUCCESS}]Y[/{UIColors.SUCCESS}]  Use DATABASE_URL (recommended for production)")
        console.print(f"  [{UIColors.SUCCESS}]N[/{UIColors.SUCCESS}]  Use individual database parameters")
        console.print()

        return CharReader.get_yes_no(f"[{UIColors.HIGHLIGHT}]Use DATABASE_URL? (Y/n):[/{UIColors.HIGHLIGHT}]") == "y"

    def get_database_type_choice(self) -> str:
        console.print()
        console.print(f"[{UIColors.INFO}]Select Database Type[/{UIColors.INFO}]\n")
        console.print(f"  [{UIColors.SUCCESS}]1[/{UIColors.SUCCESS}]  PostgreSQL")
        console.print(f"  [{UIColors.SUCCESS}]2[/{UIColors.SUCCESS}]  MySQL")
        console.print()

        choice = CharReader.get_validated_char_input(
            f"[{UIColors.HIGHLIGHT}]Choose database (1/2):[/{UIColors.HIGHLIGHT}]",
            valid_keys=["1", "2"],
            default=None,
            error_message="Invalid input '{response}'. Please enter '1' or '2'.",
        )

        return "mysql" if choice == "2" else "postgresql"

    def _get_structure_metadata(
        self,
        project_dir: str,
        predefined: bool = False,
        unified: bool = False,
        single: bool = False,
        single_module_name: str = None,
        database_type: str = "postgresql",
        use_database_url: bool = True,
        use_github: bool = False,
        use_gitlab: bool = False,
    ) -> Tuple[str, str, list[str], dict]:
        """Helper method to generate metadata dictionary."""
        project_name = project_dir
        app_names: list[str] = []

        # Default package_name to "backend" if project_dir is "." or empty
        package_name = get_package_name(project_dir)

        project_module_name = "config" if predefined else "core" if unified else None

        if single:
            project_module_name = single_module_name or "project"

        metadata = ProjectMetadata(
            package_name=package_name,
            use_github_actions=use_github,
            use_gitlab_ci=use_gitlab,
            nested_apps=True,
            nested_dir="apps",
            use_database_url=use_database_url,
            database_type=database_type,
            predefined_structure=predefined,
            unified_structure=unified,
            single_structure=single,
            project_module_name=project_module_name,
        )

        return project_name, "", app_names, metadata.to_dict()


class CharReader:
    MAX_ATTEMPTS = 3

    @staticmethod
    def get_char() -> str:
        if os.name == "nt":
            return CharReader._get_char_windows()
        return CharReader._get_char_unix()

    @staticmethod
    def _is_enter_key(response: str) -> bool:
        """Check if response represents Enter key or control character."""
        return not response or response in ("\r", "\n") or ord(response) < 32

    @staticmethod
    def _get_char_input(prompt: str) -> str:
        console.print(f"{prompt} ", end="")
        sys.stdout.flush()
        return CharReader().get_char()

    @staticmethod
    def _handle_default(default: str) -> str:
        console.print(default.upper())
        return default.lower()

    @staticmethod
    def get_validated_char_input(
        prompt: str,
        valid_keys: list[str],
        default: str | None,
        error_message: str,
    ) -> str:
        attempt = 0
        valid_keys_lower = [k.lower() for k in valid_keys]

        while attempt < CharReader.MAX_ATTEMPTS:
            try:
                response = CharReader._get_char_input(prompt)

                # Handle Enter key (default)
                if CharReader._is_enter_key(response):
                    if default is not None:
                        return CharReader._handle_default(default)
                    # If default is None, treat as invalid input (fall through)

                response = response.lower()

                # Validate response
                if response in valid_keys_lower:
                    console.print(response.upper())
                    return response

                # Invalid input - show error
                console.print()
                if response.isprintable():
                    UIFormatter.print_error(error_message.format(response=response))
                    attempt += 1
                    if attempt < CharReader.MAX_ATTEMPTS:
                        console.print(
                            f"[{UIColors.MUTED}]Please try again ({attempt}/{CharReader.MAX_ATTEMPTS}).[/{UIColors.MUTED}]"
                        )
                        console.print()
                else:
                    # Control character entered (e.g. Enter with no default)
                    if default is not None:
                        return CharReader._handle_default(default)

                    UIFormatter.print_error("Input required.")
                    attempt += 1
                    if attempt < CharReader.MAX_ATTEMPTS:
                        console.print(
                            f"[{UIColors.MUTED}]Please try again ({attempt}/{CharReader.MAX_ATTEMPTS}).[/{UIColors.MUTED}]"
                        )
                        console.print()

            except KeyboardInterrupt:
                console.print()
                UIFormatter.print_info("\nOperation cancelled by user.")
                raise

        # Max attempts reached
        console.print()
        if default is not None:
            UIFormatter.print_warning(f"Maximum attempts reached. Using default: '{default.upper()}'.")
            return default.lower()

        UIFormatter.print_error("Maximum attempts reached. Exiting.")
        sys.exit(1)

    @staticmethod
    def get_yes_no(prompt: str, default: str = None) -> str:
        if default is None:
            if "(Y/n)" in prompt or "(Y/N)" in prompt:
                default = "y"
            elif "(y/N)" in prompt:
                default = "n"
            else:
                default = "y"

        return CharReader.get_validated_char_input(
            prompt=prompt,
            valid_keys=["y", "n"],
            default=default,
            error_message="Invalid input '{response}'. Please enter 'y' or 'n'.",
        )

    @staticmethod
    def get_cicd_choice(prompt: str, valid_keys: list[str], default: str = "n") -> str:
        valid_keys_str = ", ".join(f"'{k}'" for k in valid_keys)
        return CharReader.get_validated_char_input(
            prompt=prompt,
            valid_keys=valid_keys,
            default=default,
            error_message=f"Invalid input '{{response}}'. Please enter one of: {valid_keys_str}.",
        )

    @staticmethod
    def get_structure_choice() -> str:
        """Get structure type choice without requiring Enter key."""
        return CharReader.get_validated_char_input(
            prompt=f"[{UIColors.HIGHLIGHT}]Choose structure type (1/2/3/4) [default: 1]:[/{UIColors.HIGHLIGHT}]",
            valid_keys=["1", "2", "3", "4"],
            default="1",
            error_message="Invalid input '{response}'. Please enter '1', '2', '3', or '4'.",
        )

    @staticmethod
    def _get_char_windows() -> str:
        import msvcrt

        encodings = ["utf-8", "latin1"]

        for encoding in encodings:
            try:
                ch = msvcrt.getch()
                if isinstance(ch, bytes):
                    if ch == b"\x03":
                        raise KeyboardInterrupt
                    decoded = ch.decode(encoding).lower()
                else:
                    if ord(ch) == 3:  # Ctrl+C
                        raise KeyboardInterrupt
                    decoded = ch.lower()
                return decoded
            except (UnicodeDecodeError, AttributeError):
                continue

        # Fallback
        try:
            ch = msvcrt.getch()
            if isinstance(ch, bytes):
                if ch == b"\x03":
                    raise KeyboardInterrupt
                return ch.decode("utf-8", errors="ignore").lower()
            else:
                if ord(ch) == 3:  # Ctrl+C
                    raise KeyboardInterrupt
                return ch.lower()
        except KeyboardInterrupt:
            raise
        except Exception:
            return ""

    @staticmethod
    def _get_char_unix() -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ord(ch) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_user_input() -> Tuple[str, str, str, list, dict]:
    try:
        collector = InputCollector()
        console.print()

        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Choose Structure Type[/{UIColors.INFO}]\n")
        console.print(f"[{UIColors.MUTED}]1. Standard structure (default Django layout)[/{UIColors.MUTED}]")
        console.print(f"[{UIColors.MUTED}]2. Predefined structure (apps/users, apps/core, api/)[/{UIColors.MUTED}]")
        console.print(f"[{UIColors.MUTED}]3. Unified structure (core/, apps/core, apps/api)[/{UIColors.MUTED}]")
        console.print(f"[{UIColors.MUTED}]4. Single folder layout (everything in one folder)[/{UIColors.MUTED}]")
        console.print()

        structure_choice = CharReader.get_structure_choice()

        use_standard = structure_choice == "1"
        use_predefined = structure_choice == "2"
        use_unified = structure_choice == "3"
        use_single = structure_choice == "4"

        # Step 1: Project Setup
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Step 1: Project Setup[/{UIColors.INFO}]\n")
        console.print(f"[{UIColors.MUTED}]Press Enter or enter '.' to create in current directory[/{UIColors.MUTED}]")

        project_dir = collector._get_project_directory()
        if project_dir is None:
            UIFormatter.print_error("Maximum attempts reached for project directory name. Exiting.")
            sys.exit(1)

        project_name = project_dir
        single_module_name = None

        if use_standard:
            console.print()
            console.print(f"[{UIColors.MUTED}]Common names: config, core, settings[/{UIColors.MUTED}]")
            project_name = collector.get_validated_input(
                "Enter Django project name", validate_project_name, "Django project name"
            )
        elif use_single:
            console.print()
            console.print(f"[{UIColors.MUTED}]Common names: project, core, app[/{UIColors.MUTED}]")
            single_module_name = (
                collector.get_validated_input(
                    "Enter project configuration directory name (default: project)",
                    validate_project_name,
                    "directory name",
                    allow_empty=True,
                )
                or "project"
            )

        # Step 2: Database Configuration
        console.print()
        UIFormatter.print_separator()
        console.print(f"\n[{UIColors.INFO}]Step 2: Database Configuration[/{UIColors.INFO}]")
        database_type = collector.get_database_type_choice()
        use_database_url = collector.get_database_config_choice()

        # Step 3: Django Apps (Standard only)
        nested = False
        nested_dir = None
        app_names = []

        if use_standard:
            console.print()
            UIFormatter.print_separator()
            console.print(f"\n[{UIColors.INFO}]Step 3: Django Apps[/{UIColors.INFO}]\n")
            nested, nested_dir = collector.get_nested_apps_config()
            app_names = collector.get_app_names()

        # Step 3/4: CI/CD Pipeline
        step_num = 4 if use_standard else 3
        console.print(f"\n[{UIColors.INFO}]Step {step_num}: CI/CD Pipeline[/{UIColors.INFO}]")
        use_github, use_gitlab = collector.get_cicd_choice()

        # Generate Metadata
        if use_standard:
            package_name = get_package_name(project_dir)
            metadata = ProjectMetadata(
                package_name=package_name,
                use_github_actions=use_github,
                use_gitlab_ci=use_gitlab,
                nested_apps=nested,
                nested_dir=nested_dir,
                use_database_url=use_database_url,
                database_type=database_type,
            )
            return project_dir, project_name, app_names[0], app_names, metadata.to_dict()
        else:
            project_name, primary_app, app_names, metadata_dict = collector._get_structure_metadata(
                project_dir,
                predefined=use_predefined,
                unified=use_unified,
                single=use_single,
                single_module_name=single_module_name,
                database_type=database_type,
                use_database_url=use_database_url,
                use_github=use_github,
                use_gitlab=use_gitlab,
            )
            return project_dir, project_name, primary_app, app_names, metadata_dict

    except KeyboardInterrupt:
        UIFormatter.print_info("\nSetup cancelled by user.")
        sys.exit(0)


def confirm_setup(project_dir: str, project_name: str, app_names: list, metadata: dict) -> bool:
    console.print()
    UIFormatter.print_separator()
    console.print()
    console.print(f"[{UIColors.INFO}]Setup Summary[/{UIColors.INFO}]")
    console.print()

    console.print(f"[{UIColors.HIGHLIGHT}]Project Directory:[/{UIColors.HIGHLIGHT}] {project_dir}")
    console.print(f"[{UIColors.HIGHLIGHT}]Django Project:[/{UIColors.HIGHLIGHT}] {project_name}")
    console.print(f"[{UIColors.HIGHLIGHT}]Apps:[/{UIColors.HIGHLIGHT}] {', '.join(app_names)}")
    console.print(f"[{UIColors.HIGHLIGHT}]Package:[/{UIColors.HIGHLIGHT}] {metadata['package_name']}")

    cicd_choices = _get_cicd_display(metadata)
    console.print(f"[{UIColors.HIGHLIGHT}]CI/CD:[/{UIColors.HIGHLIGHT}] {cicd_choices}")

    db_config = "DATABASE_URL" if metadata.get("use_database_url", True) else "Individual parameters"
    console.print(f"[{UIColors.HIGHLIGHT}]Database Config:[/{UIColors.HIGHLIGHT}] {db_config}")

    db_type = metadata.get("database_type", "postgresql").capitalize()
    console.print(f"[{UIColors.HIGHLIGHT}]Database Type:[/{UIColors.HIGHLIGHT}] {db_type}")

    console.print()
    UIFormatter.print_separator()
    console.print()

    try:
        response = CharReader.get_yes_no(f"[{UIColors.WARNING}]Proceed with setup? (y/N):[/{UIColors.WARNING}]")
        return response == "y"

    except KeyboardInterrupt:
        UIFormatter.print_info("\nSetup cancelled by user.")
        return False


def _get_cicd_display(metadata: dict) -> str:
    choices = []
    if metadata.get("use_github_actions", False):
        choices.append("GitHub Actions")
    if metadata.get("use_gitlab_ci", False):
        choices.append("GitLab CI")
    return ", ".join(choices) if choices else "None"


get_char = CharReader.get_char
_get_validated_input = InputCollector().get_validated_input
