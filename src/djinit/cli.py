import logging
from typing import Annotated, Optional

import typer
from rich.panel import Panel
from rich.text import Text

from djinit.creators.app import AppCreator
from djinit.creators.setup import SetupCreator
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.ui.input import get_user_input
from djinit.utils.secretkey import display_secret_keys, generate_multiple_keys
from djinit.utils.validators import validate_app_name

# Configure logger
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="djinit - A CLI tool to set up Django projects with best practices.",
    add_completion=False,
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        try:
            typer.echo(f"djinit v{version('djinitx')}")
        except Exception:
            typer.echo("djinit (version unknown)")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True, help="Show the version and exit."),
    ] = None,
):
    """
    djinit: Django Project Initializer
    """
    pass


@app.command("secret")
def secret(
    count: Annotated[int, typer.Option("--count", "-c", help="Number of keys to generate")] = 3,
    length: Annotated[int, typer.Option("--length", "-l", help="Length of each secret key")] = 50,
):
    """
    Generate Django secret keys.
    """
    keys = generate_multiple_keys(count, length)
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


@app.command("app")
def create_app(app_names: Annotated[list[str], typer.Argument(help="Name(s) of the Django app(s) to create")]):
    """
    Create one or more Django apps.
    """
    UIFormatter.print_info("")
    UIFormatter.print_header("Django App Creation")
    UIFormatter.print_info("")

    # Process app names (handle commma separation if passed as single arg)
    processed_names = []
    for name in app_names:
        parts = [p.strip() for p in name.split(",") if p.strip()]
        processed_names.extend(parts)

    processed_names = list(dict.fromkeys(processed_names))  # Dedup

    if not processed_names:
        UIFormatter.print_error("App name cannot be empty")
        raise typer.Exit(1)

    for name in processed_names:
        is_valid, error_msg = validate_app_name(name)
        if not is_valid:
            UIFormatter.print_error(f"Invalid app name '{name}': {error_msg}")
            raise typer.Exit(1)

    any_failure = False
    for name in processed_names:
        creator = AppCreator(name)
        success = creator.create_app()
        if not success:
            UIFormatter.print_error(f"Failed to create Django app '{name}'")
            any_failure = True
            break  # Stop on failure? Or continue? Original code broke loop on failure.

    if any_failure:
        raise typer.Exit(1)

    instructions = Text()
    instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
    instructions.append("1. The app(s) have been added to INSTALLED_APPS in settings/base.py\n")
    instructions.append("2. Create your models in each app's models.py\n")
    instructions.append("3. Run migrations: just makemigrations\n")
    instructions.append("4. Apply migrations: just migrate\n")
    instructions.append("5. Create views, serializers and routes(URLs) for your app(s)\n")

    console.print(Panel(instructions, title="💡 What's Next", border_style="green"))
    UIFormatter.print_info("")


@app.command("setup")
def setup():
    """
    Interactively set up a new Django project.
    """
    UIFormatter.print_header("Django Project Setup")

    project_dir, project_name, primary_app, app_names, metadata = get_user_input()

    orchestrator = SetupCreator(project_dir, project_name, primary_app, app_names, metadata)
    success = orchestrator.create()

    if success:
        UIFormatter.print_info("")
        UIFormatter.print_header("Setup Complete!")
        console.print(f"[bold green]Project '{project_name}' has been successfully created![/bold green]")

        instructions = Text()
        instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
        instructions.append(f"1. cd {project_dir}\n")
        instructions.append("2. Install dependencies: pip install -r requirements.txt\n")
        instructions.append("3. Run migrations: just migrate (or python manage.py migrate)\n")
        instructions.append("4. Start server: just run (or python manage.py runserver)\n")

        console.print(Panel(instructions, title="Get Started", border_style="green"))
    else:
        UIFormatter.print_error("Project setup failed. Please check the logs above.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
