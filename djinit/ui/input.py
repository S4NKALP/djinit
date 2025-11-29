"""
User input handling for Django project setup.
Handles collection and processing of user inputs during setup.
"""

import os
import sys
from typing import Tuple, TypedDict

import questionary

from djinit.core.types import ProjectMetadata
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.utils.common import get_package_name
from djinit.utils.validators import validate_app_name, validate_project_name


class StructureOptions(TypedDict):
    project_dir: str
    predefined: bool
    unified: bool
    single: bool
    single_module_name: str | None
    database_type: str
    use_database_url: bool
    use_github: bool
    use_gitlab: bool


class InputCollector:
    def __init__(self):
        pass

    def get_validated_input(self, prompt: str, validator: callable, input_type: str, allow_empty: bool = False) -> str:
        def q_validator(text):
            if not text and allow_empty:
                return True
            if not text:
                return f"{input_type.capitalize()} cannot be empty"
            is_valid, error_msg = validator(text)
            if is_valid:
                return True
            return error_msg

        result = questionary.text(prompt, validate=q_validator).ask()
        if result is None:
            raise KeyboardInterrupt
        return result

    def get_app_names(self) -> list[str]:
        user_input = questionary.text(
            "Enter app names (comma-separated or single, e.g. users, products, orders):",
            validate=lambda text: True if text.strip() else "At least one app name is required",
        ).ask()

        if user_input is None:
            raise KeyboardInterrupt

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
        def validate_dir(text):
            if not text or text == ".":
                return True

            is_valid, error_msg = validate_project_name(text)
            if not is_valid:
                return error_msg

            if os.path.exists(text):
                return f"Directory '{text}' already exists."

            return True

        project_dir = questionary.text("Enter project directory name:", validate=validate_dir).ask()

        if project_dir is None:
            raise KeyboardInterrupt

        if not project_dir or project_dir == ".":
            UIFormatter.print_info(f"Creating project in current directory: {os.getcwd()}")
            return "."

        return project_dir

    def _get_selection(self, message: str, choices: list[tuple[str, str]], default: str = None) -> str:
        q_choices = [questionary.Choice(title, value=value) for title, value in choices]
        default_choice = next((c for c in q_choices if c.value == default), q_choices[0])

        result = questionary.select(
            message,
            choices=q_choices,
            default=default_choice,
        ).ask()

        if result is None:
            raise KeyboardInterrupt

        return result

    def get_cicd_choice(self) -> Tuple[bool, bool]:
        choices = [
            ("None (skip CI/CD)", "none"),
            ("GitHub Actions only", "github"),
            ("GitLab CI only", "gitlab"),
            ("Both (GitHub Actions + GitLab CI)", "both"),
        ]

        choice = self._get_selection("Select CI/CD pipeline:", choices, default="none")

        choice_map = {
            "both": (True, True),
            "github": (True, False),
            "gitlab": (False, True),
            "none": (False, False),
        }
        return choice_map.get(choice, (False, False))

    def get_nested_apps_config(self) -> Tuple[bool, str | None]:
        choice = UIFormatter.confirm(
            "Do you want to place apps inside a package directory (e.g. 'src/')?", default=False
        )

        if not choice:
            return False, None

        dir_name = self.get_validated_input(
            "Enter directory name for apps package (e.g. src)",
            validate_project_name,
            "apps package name",
        )
        return True, dir_name

    def get_database_config_choice(self) -> bool:
        return UIFormatter.confirm("Use DATABASE_URL? (recommended for production)", default=True)

    def get_database_type_choice(self) -> str:
        choices = [
            ("PostgreSQL", "postgresql"),
            ("MySQL", "mysql"),
        ]

        return self._get_selection("Choose database:", choices, default="postgresql")

    def _get_structure_metadata(self, options: StructureOptions) -> Tuple[str, str, list[str], dict]:
        """Helper method to generate metadata dictionary."""
        project_dir = options["project_dir"]
        project_name = project_dir
        app_names: list[str] = []

        # Default package_name to "backend" if project_dir is "." or empty
        package_name = get_package_name(project_dir)

        project_module_name = "config" if options["predefined"] else "core" if options["unified"] else None

        if options["single"]:
            project_module_name = options["single_module_name"] or "project"

        metadata = ProjectMetadata(
            package_name=package_name,
            use_github_actions=options["use_github"],
            use_gitlab_ci=options["use_gitlab"],
            nested_apps=not options["single"],
            nested_dir="apps" if not options["single"] else None,
            use_database_url=options["use_database_url"],
            database_type=options["database_type"],
            predefined_structure=options["predefined"],
            unified_structure=options["unified"],
            single_structure=options["single"],
            project_module_name=project_module_name,
        )

        return project_name, "", app_names, metadata.to_dict()


def get_user_input() -> Tuple[str, str, str, list, dict]:
    try:
        collector = InputCollector()

        structure_choices = [
            ("Standard structure (default Django layout)", "1"),
            ("Predefined structure (apps/users, apps/core, api/)", "2"),
            ("Unified structure (core/, apps/core, apps/api)", "3"),
            ("Single folder layout (everything in one folder)", "4"),
        ]

        structure_choice = collector._get_selection("Choose structure type:", structure_choices, default="1")

        use_standard = structure_choice == "1"
        use_predefined = structure_choice == "2"
        use_unified = structure_choice == "3"
        use_single = structure_choice == "4"

        # Step 1: Project Setup
        project_dir = collector._get_project_directory()
        if project_dir is None:
            # Should be handled by questionary loop, but just in case
            sys.exit(1)

        project_name = project_dir
        single_module_name = None

        if use_standard:
            console.print(f"[{UIColors.MUTED}]Common names: config, core, settings[/{UIColors.MUTED}]")
            project_name = collector.get_validated_input(
                "Enter Django project name", validate_project_name, "Django project name"
            )
        elif use_single:
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
        database_type = collector.get_database_type_choice()
        use_database_url = collector.get_database_config_choice()

        # Step 3: Django Apps (Standard only)
        nested = False
        nested_dir = None
        app_names = []

        if use_standard:
            nested, nested_dir = collector.get_nested_apps_config()
            app_names = collector.get_app_names()

        # Step 3/4: CI/CD Pipeline
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
            options = StructureOptions(
                project_dir=project_dir,
                predefined=use_predefined,
                unified=use_unified,
                single=use_single,
                single_module_name=single_module_name,
                database_type=database_type,
                use_database_url=use_database_url,
                use_github=use_github,
                use_gitlab=use_gitlab,
            )
            project_name, primary_app, app_names, metadata_dict = collector._get_structure_metadata(options)
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
        return UIFormatter.confirm("Proceed with setup?", default=True)

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
