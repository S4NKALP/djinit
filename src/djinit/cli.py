import logging
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Optional

import questionary
import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from djinit.core.manifest import ManifestManager
from djinit.core.template_manager import NAME_REGEX, CustomTemplateManager
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


@app.command("help")
def help_command(
    ctx: typer.Context,
    command: Annotated[
        Optional[str],
        typer.Argument(help="Specific command to show detailed help for (e.g. setup, app, secret, template)."),
    ] = None,
):
    """
    Show help and command reference for djinit.
    """
    click_app = typer.main.get_command(app)

    if not command:
        UIFormatter.print_info("")
        UIFormatter.print_header("djinit - Django Project Initializer CLI")
        console.print(
            "[dim]A CLI tool to set up, scaffold, and manage modern Django projects with best practices.[/dim]\n"
        )

        table = Table(title="Available Commands & Subcommands", border_style="cyan")
        table.add_column("Command", style="bold green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Usage / Syntax", style="dim")

        table.add_row(
            "setup",
            "Interactively set up a new Django project or bootstrap from template",
            "djinit setup [--template <name>] [--name <proj>] [--dir <dir>]",
        )
        table.add_row(
            "app",
            "Generate one or more architecture-aware Django apps",
            "djinit app <app_name> [app2...]",
        )
        table.add_row(
            "secret",
            "Generate cryptographically secure Django SECRET_KEY tokens",
            "djinit secret [--count <n>] [--length <len>]",
        )
        table.add_row(
            "template export",
            "Export an existing project as a sanitized starter template",
            "djinit template export [dir] [--name <name>] [--force]",
        )
        table.add_row(
            "template list",
            "List all saved custom project templates",
            "djinit template list",
        )
        table.add_row(
            "template apply",
            "Bootstrap a new Django project from a saved custom template",
            "djinit template apply <template_name> [--name <proj>] [--dir <dir>]",
        )
        table.add_row(
            "template delete",
            "Delete a saved custom template",
            "djinit template delete <template_name> [--force]",
        )
        table.add_row(
            "help",
            "Show this command overview or detailed help for a specific command",
            "djinit help [command]",
        )

        console.print(table)
        console.print()

        examples = Text()
        examples.append("💡 Quick Examples:\n", style=UIColors.ACCENT)
        examples.append(
            "  djinit                                 # Start interactive project setup wizard\n",
            style=UIColors.CODE,
        )
        examples.append(
            "  djinit app users orders                # Create 2 architecture-aware Django apps\n",
            style=UIColors.CODE,
        )
        examples.append(
            "  djinit template export                 # Export current project via interactive wizard\n",
            style=UIColors.CODE,
        )
        examples.append(
            "  djinit setup --template my-starter     # Scaffold new project from custom template\n",
            style=UIColors.CODE,
        )
        examples.append(
            "  djinit help <command>                  # Detailed help for specific command\n",
            style=UIColors.CODE,
        )
        console.print(Panel(examples, title="Usage Shortcuts", border_style="green"))
        console.print()
        return

    sub_cmd = click_app.get_command(ctx, command)
    if sub_cmd:
        sub_ctx = typer.Context(sub_cmd, info_name=f"djinit {command}", parent=ctx)
        console.print(sub_cmd.get_help(sub_ctx))
    else:
        UIFormatter.print_error(f"Unknown command '{command}'.")
        console.print(
            "Run [bold cyan]djinit help[/bold cyan] or [bold cyan]djinit --help[/bold cyan] to see available commands.\n"
        )
        raise typer.Exit(1)


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


def _interactive_export_wizard(
    source_dir: str | None = None,
    name: str | None = None,
    description: str | None = None,
    force: bool = False,
) -> tuple[Path, str, str, bool]:
    """Interactive questionary wizard for exporting custom project templates."""
    UIFormatter.print_info("")
    UIFormatter.print_header("Export Custom Django Template")
    UIFormatter.print_info("Transform an existing Django project into a reusable starter template.\n")

    # 1. Source project directory
    if not source_dir:

        def validate_src(val: str):
            val = val.strip() or "."
            p = Path(val).resolve()
            if not p.is_dir():
                return f"Directory '{val}' does not exist."
            if not (p / "manage.py").is_file():
                return f"'{val}' is not a valid Django project (missing manage.py)."
            return True

        source_input = questionary.text(
            "Enter path to Django project to export:",
            default=".",
            validate=validate_src,
        ).ask()
        if source_input is None:
            raise KeyboardInterrupt
        source_path = Path(source_input.strip() or ".").resolve()
    else:
        source_path = Path(source_dir).resolve()
        if not (source_path / "manage.py").is_file():
            UIFormatter.print_error(f"'{source_path}' is not a valid Django project (missing manage.py).")
            raise typer.Exit(1)

    # Detect default template name
    default_name = source_path.name
    manifest = ManifestManager.load_manifest(str(source_path))
    if manifest and manifest.project and manifest.project.name:
        default_name = manifest.project.name

    # 2. Template name
    if not name:

        def validate_name(val: str):
            val = val.strip()
            if not val:
                return "Template name cannot be empty."
            if not NAME_REGEX.match(val):
                return "Name must contain only letters, numbers, underscores, and hyphens."
            return True

        template_name = questionary.text(
            "Enter unique name for this template:",
            default=default_name,
            validate=validate_name,
        ).ask()
        if template_name is None:
            raise KeyboardInterrupt
        template_name = template_name.strip()
    else:
        template_name = name.strip()
        if not NAME_REGEX.match(template_name):
            UIFormatter.print_error(f"Invalid template name '{template_name}'.")
            raise typer.Exit(1)

    # 3. Handle overwrite if already exists
    target_force = force
    if CustomTemplateManager.get_template(template_name) and not force:
        confirm_overwrite = questionary.confirm(
            f"Template '{template_name}' already exists. Overwrite?",
            default=False,
        ).ask()
        if confirm_overwrite is None:
            raise KeyboardInterrupt
        if not confirm_overwrite:
            UIFormatter.print_info("Export cancelled.")
            raise typer.Exit(0)
        target_force = True

    # 4. Description
    if description is None or description == "":
        desc_input = questionary.text(
            "Enter template description (optional):",
            default=f"Template exported from {default_name}",
        ).ask()
        if desc_input is None:
            raise KeyboardInterrupt
        template_desc = desc_input.strip()
    else:
        template_desc = description.strip()

    # 5. Summary & Confirmation
    target_path = CustomTemplateManager.get_templates_root() / template_name
    console.print()
    UIFormatter.print_separator()
    console.print()
    console.print(f"[{UIColors.INFO}]Template Export Summary[/{UIColors.INFO}]")
    console.print()
    console.print(f"[{UIColors.HIGHLIGHT}]Source Directory:[/{UIColors.HIGHLIGHT}] {source_path}")
    console.print(f"[{UIColors.HIGHLIGHT}]Template Name:[/{UIColors.HIGHLIGHT}] {template_name}")
    console.print(f"[{UIColors.HIGHLIGHT}]Description:[/{UIColors.HIGHLIGHT}] {template_desc}")
    console.print(f"[{UIColors.HIGHLIGHT}]Destination:[/{UIColors.HIGHLIGHT}] {target_path}")
    console.print(
        f"[{UIColors.HIGHLIGHT}]Sanitization:[/{UIColors.HIGHLIGHT}] Ignores .venv, caches, db.sqlite3, masks SECRET_KEY"
    )
    console.print()
    UIFormatter.print_separator()
    console.print()

    proceed = questionary.confirm("Proceed with template export?", default=True).ask()
    if proceed is None or not proceed:
        UIFormatter.print_info("\nExport cancelled by user.")
        raise typer.Exit(0)

    return source_path, template_name, template_desc, target_force


@template_app.command("export")
def export_template(
    source_dir: Annotated[
        Optional[str],
        typer.Argument(help="Path to the Django project to export (defaults to current directory if not prompted)."),
    ] = None,
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
    Shows an interactive wizard with Questionary prompts when options are omitted.
    """
    try:
        if not name:
            source_path, template_name, template_desc, should_overwrite = _interactive_export_wizard(
                source_dir=source_dir,
                name=name,
                description=description,
                force=force,
            )
        else:
            source_path = Path(source_dir or ".").resolve()
            if not (source_path / "manage.py").is_file():
                UIFormatter.print_error(f"'{source_path}' is not a valid Django project (missing manage.py).")
                raise typer.Exit(1)
            template_name = name.strip()
            template_desc = description
            should_overwrite = force
    except KeyboardInterrupt:
        UIFormatter.print_info("\nExport cancelled by user.")
        raise typer.Exit(0) from None

    try:
        exported_path = CustomTemplateManager.export_template(
            source_dir=source_path,
            template_name=template_name,
            description=template_desc,
            overwrite=should_overwrite,
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


@template_app.command("help")
def template_help_cmd(ctx: typer.Context):
    """
    Show help for custom template commands.
    """
    click_template = typer.main.get_command(template_app)
    sub_ctx = typer.Context(click_template, info_name="djinit template", parent=ctx)
    console.print(click_template.get_help(sub_ctx))


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
