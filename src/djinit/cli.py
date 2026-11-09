import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from djinit.core.manifest import ManifestManager
from djinit.core.template_manager import CustomTemplateManager
from djinit.creators.app import AppCreator
from djinit.creators.setup import SetupCreator
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.ui.input import get_user_input
from djinit.utils.secretkey import display_secret_keys, generate_multiple_keys
from djinit.utils.validators import validate_app_name, validate_project_name

# Configure logger
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="djinit - A CLI tool to set up Django projects with best practices.",
    add_completion=False,
    no_args_is_help=False,
)

template_app = typer.Typer(
    name="template",
    help="Manage and export custom reusable project templates.",
    no_args_is_help=False,
)
app.add_typer(template_app, name="template")


def version_callback(value: bool):
    if value:
        from importlib.metadata import version

        try:
            typer.echo(f"djinit v{version('djinitx')}")
        except Exception:
            typer.echo("djinit (version unknown)")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True, help="Show the version and exit."),
    ] = None,
):
    """
    djinit: Django Project Initializer
    """
    if ctx.invoked_subcommand is None:
        setup()


@app.command("secret")
def secret(
    count: Annotated[int, typer.Option("--count", "-c", help="Number of keys to generate")] = 3,
    length: Annotated[int, typer.Option("--length", "-l", help="Length of each secret key")] = 50,
):
    """
    Generate Django secret keys.
    """
    if length < 16:
        UIFormatter.print_warning("Secret key length increased to minimum recommended length (16 characters).")
        length = 16
    if count < 1:
        count = 1

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


def _apply_template_flow(
    template_name: str,
    project_name: str | None = None,
    project_dir: str | None = None,
) -> None:
    """Helper to instantiate a project from a custom template."""
    import questionary

    if not CustomTemplateManager.get_template(template_name):
        UIFormatter.print_error(f"Template '{template_name}' not found.")
        UIFormatter.print_info("Use 'djinit template list' to view available templates.")
        raise typer.Exit(1)

    if not project_name:
        project_name = questionary.text(
            "Enter project name:",
            validate=lambda val: True if validate_project_name(val)[0] else validate_project_name(val)[1],
        ).ask()
        if not project_name:
            raise typer.Exit(1)
    else:
        is_valid, err = validate_project_name(project_name)
        if not is_valid:
            UIFormatter.print_error(f"Invalid project name '{project_name}': {err}")
            raise typer.Exit(1)

    if not project_dir:
        project_dir = f"./{project_name}"

    dest_path = Path(project_dir).resolve()
    if dest_path.exists() and any(dest_path.iterdir()):
        UIFormatter.print_error(f"Directory '{dest_path}' already exists and is not empty.")
        raise typer.Exit(1)

    UIFormatter.print_header(f"Creating project '{project_name}' from template '{template_name}'")
    success = CustomTemplateManager.apply_template(template_name, dest_path, project_name)
    if success:
        instructions = Text()
        instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
        instructions.append(f"1. cd {project_dir}\n")
        instructions.append("2. Install dependencies: pip install -r requirements.txt (or uv sync)\n")
        instructions.append("3. Run migrations: python manage.py migrate\n")
        instructions.append("4. Start server: python manage.py runserver\n")
        console.print(Panel(instructions, title="Get Started", border_style="green"))
    else:
        raise typer.Exit(1)


@template_app.callback(invoke_without_command=True)
def template_main(ctx: typer.Context):
    """
    Manage and export custom reusable project templates.
    """
    if ctx.invoked_subcommand is None:
        list_templates()


@template_app.command("list")
def list_templates():
    """
    List all available custom templates.
    """
    templates = CustomTemplateManager.list_templates()
    if not templates:
        UIFormatter.print_info("")
        UIFormatter.print_warning("No custom templates found.")
        UIFormatter.print_info("Export your current project using:")
        console.print("  [bold cyan]djinit template export . --name <template-name>[/bold cyan]\n")
        return

    table = Table(title="Custom Project Templates", border_style="cyan")
    table.add_column("Name", style="bold green")
    table.add_column("Description", style="white")
    table.add_column("Source Project", style="dim")
    table.add_column("Created", style="dim")

    for t in templates:
        created = t.get("created_at", "")
        if "T" in created:
            created = created.split("T")[0]
        table.add_row(
            t.get("name", ""),
            t.get("description", ""),
            t.get("source_project", "unknown"),
            created,
        )

    UIFormatter.print_info("")
    console.print(table)
    console.print()


@template_app.command("export")
def export_template(
    source_dir: Annotated[
        str,
        typer.Argument(help="Path to the Django project to export (defaults to current directory)."),
    ] = ".",
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Unique template name."),
    ] = None,
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Short description of the template."),
    ] = "",
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite if template name already exists."),
    ] = False,
):
    """
    Export an existing Django project as a reusable custom template.
    """
    import questionary

    source_path = Path(source_dir).resolve()
    if not (source_path / "manage.py").is_file():
        UIFormatter.print_error(f"'{source_path}' is not a valid Django project (missing manage.py).")
        raise typer.Exit(1)

    template_name = name
    if not template_name:
        default_name = source_path.name
        manifest = ManifestManager.load_manifest(str(source_path))
        if manifest and manifest.project and manifest.project.name:
            default_name = manifest.project.name
        template_name = questionary.text(
            "Enter a name for the template:",
            default=default_name,
        ).ask()
        if not template_name:
            UIFormatter.print_error("Template name cannot be empty.")
            raise typer.Exit(1)

    try:
        exported_path = CustomTemplateManager.export_template(
            source_dir=source_path,
            template_name=template_name,
            description=description,
            overwrite=force,
        )
        UIFormatter.print_info("")
        UIFormatter.print_success(f"Template '{template_name}' successfully exported!")
        console.print(f"[dim]Saved to: {exported_path}[/dim]\n")
        instructions = Text()
        instructions.append("🚀 How to use your new template:\n", style=UIColors.ACCENT)
        instructions.append(f"  djinit setup --template {template_name}\n", style=UIColors.CODE)
        instructions.append(
            f"  djinit template apply {template_name} --name my_new_project\n",
            style=UIColors.CODE,
        )
        console.print(Panel(instructions, title="Template Ready", border_style="green"))
    except FileExistsError as e:
        UIFormatter.print_error(str(e))
        UIFormatter.print_info("Use --force to overwrite an existing template.")
        raise typer.Exit(1) from None
    except Exception as e:
        UIFormatter.print_error(f"Failed to export template: {e}")
        raise typer.Exit(1) from None


@template_app.command("delete")
def delete_template(
    name: Annotated[str, typer.Argument(help="Name of the custom template to delete.")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt."),
    ] = False,
):
    """
    Delete a saved custom template.
    """
    import questionary

    template_path = CustomTemplateManager.get_template(name)
    if not template_path:
        UIFormatter.print_error(f"Template '{name}' not found.")
        raise typer.Exit(1)

    if not force:
        confirm = questionary.confirm(f"Are you sure you want to delete template '{name}'?").ask()
        if not confirm:
            UIFormatter.print_info("Deletion cancelled.")
            return

    if CustomTemplateManager.delete_template(name):
        UIFormatter.print_success(f"Template '{name}' deleted successfully.")
    else:
        UIFormatter.print_error(f"Failed to delete template '{name}'.")
        raise typer.Exit(1)


@template_app.command("apply")
def apply_template_cmd(
    template_name: Annotated[str, typer.Argument(help="Name of the custom template to use.")],
    project_name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="New project name."),
    ] = None,
    project_dir: Annotated[
        Optional[str],
        typer.Option("--dir", "-d", help="Destination directory."),
    ] = None,
):
    """
    Instantiate a new project from a custom template.
    """
    _apply_template_flow(template_name, project_name, project_dir)


@app.command("setup")
def setup(
    template: Annotated[
        Optional[str],
        typer.Option("--template", "-t", help="Name of a saved custom template to scaffold from."),
    ] = None,
    project_name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Project name (when using --template)."),
    ] = None,
    project_dir: Annotated[
        Optional[str],
        typer.Option("--dir", "-d", help="Target project directory (when using --template)."),
    ] = None,
):
    """
    Interactively set up a new Django project, or bootstrap from a custom template.
    """
    if template:
        _apply_template_flow(template, project_name, project_dir)
        return

    UIFormatter.print_header("Django Project Setup")

    project_dir_val, project_name_val, primary_app, app_names, metadata = get_user_input()

    orchestrator = SetupCreator(project_dir_val, project_name_val, primary_app, app_names, metadata)
    success = orchestrator.create()

    if success:
        UIFormatter.print_info("")
        UIFormatter.print_header("Setup Complete!")
        console.print(f"[bold green]Project '{project_name_val}' has been successfully created![/bold green]")

        instructions = Text()
        instructions.append("🚀 Next Steps:\n", style=UIColors.ACCENT)
        instructions.append(f"1. cd {project_dir_val}\n")
        instructions.append("2. Install dependencies: pip install -r requirements.txt\n")
        instructions.append("3. Run migrations: just migrate (or python manage.py migrate)\n")
        instructions.append("4. Start server: just run (or python manage.py runserver)\n")

        console.print(Panel(instructions, title="Get Started", border_style="green"))
    else:
        UIFormatter.print_error("Project setup failed. Please check the logs above.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
