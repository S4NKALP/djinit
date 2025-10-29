"""
Console UI utilities for djinit.
Provides enhanced styling, formatting, and user interface components.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()


class UIColors:
    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold blue"
    HIGHLIGHT = "bold cyan"
    MUTED = "dim white"
    ACCENT = "bold magenta"
    PRIMARY = "bold white"
    SECONDARY = "bright_white"
    CODE = "dim cyan"
    GRADIENT_START = "rgb(139,92,246)"
    GRADIENT_END = "rgb(236,72,153)"


class Icons:
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    ROCKET = "🚀"
    PACKAGE = "📦"
    FOLDER = "📁"
    FILE = "📄"
    SETTINGS = "⚙"
    DATABASE = "🗄"
    LINK = "🔗"
    STAR = "⭐"
    FIRE = "🔥"
    SPARKLES = "✨"
    PARTY = "🎉"
    TARGET = "🎯"
    MAGNIFIER = "🔍"
    WRENCH = "🔧"
    CLOCK = "⏱"


class UIFormatter:
    """Utility class for consistent UI formatting"""

    @staticmethod
    def print_success(message: str, icon: str = Icons.SUCCESS):
        console.print(f"[{UIColors.SUCCESS}]{icon}[/{UIColors.SUCCESS}] [bold]{message}[/bold]")

    @staticmethod
    def print_error(message: str, icon: str = Icons.ERROR, details: Optional[str] = None):
        """Print error message with optional details"""
        console.print(f"[{UIColors.ERROR}]{icon}[/{UIColors.ERROR}] [bold]{message}[/bold]")
        if details:
            console.print(f"   [dim]{details}[/dim]")

    @staticmethod
    def print_warning(message: str, icon: str = Icons.WARNING):
        console.print(f"[{UIColors.WARNING}]{icon}[/{UIColors.WARNING}] [bold]{message}[/bold]")

    @staticmethod
    def print_info(message: str, icon: str = Icons.INFO):
        console.print(f"[{UIColors.INFO}]{icon}[/{UIColors.INFO}] [bold]{message}[/bold]")

    @staticmethod
    def print_step(step_number: int, total_steps: int, description: str, icon: str = ""):
        """Print step information with enhanced progress indicator"""
        icon_str = f"{icon} " if icon else ""
        percentage = int((step_number / total_steps) * 100)
        console.print(
            f"[{UIColors.HIGHLIGHT}]Step {step_number}/{total_steps}[/{UIColors.HIGHLIGHT}] "
            f"[dim]({percentage}%)[/dim] {icon_str}{description}"
        )

    @staticmethod
    def print_progress_bar(step_number: int, total_steps: int, width: int = 40):
        """Print a single progress bar that shows overall progress"""
        progress_percentage = int((step_number / total_steps) * 100)
        filled = int((step_number / total_steps) * width)
        bar = "█" * filled + "░" * (width - filled)
        console.print(
            f"\r[{UIColors.ACCENT}][{bar}][/{UIColors.ACCENT}] {progress_percentage}%",
            end="",
        )

    @staticmethod
    def create_live_progress(description: str = "Setup Progress", total_steps: int = 100):
        """Create a live progress display that updates in place"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        task = progress.add_task(description, total=total_steps)
        return progress, task

    @staticmethod
    def print_header(text: str, style: str = UIColors.PRIMARY, width: int = 70):
        """Print a styled header with customizable width"""
        console.print(f"\n[{style}]{'═' * width}[/{style}]")
        console.print(f"[{style}]{text.center(width)}[/{style}]")
        console.print(f"[{style}]{'═' * width}[/{style}]\n")

    @staticmethod
    def print_subheader(text: str, style: str = UIColors.HIGHLIGHT):
        """Print a styled subheader"""
        console.print(f"\n[{style}]{text}[/{style}]")
        console.print(f"[{UIColors.MUTED}]{'─' * len(text)}[/{UIColors.MUTED}]")

    @staticmethod
    def print_separator(char: str = "─", width: int = 70, style: str = UIColors.MUTED):
        """Print a visual separator with customization"""
        console.print(f"[{style}]{char * width}[/{style}]")

    @staticmethod
    def print_feature_list(features: List[str], icon: str = Icons.STAR):
        """Print a styled feature list with custom icons"""
        for _i, feature in enumerate(features, 1):
            console.print(f"[{UIColors.ACCENT}]  {icon}[/{UIColors.ACCENT}] [bold]{feature}[/bold]")

    @staticmethod
    def print_numbered_list(items: List[str], start: int = 1):
        """Print a numbered list with tree-style formatting"""
        total = len(items)
        for i, item in enumerate(items, start):
            prefix = "└─" if i == start + total - 1 else "├─"
            console.print(f"   [dim]{prefix}[/dim] [dim]{i}.[/dim] {item}")

    @staticmethod
    def print_tree_item(text: str, is_last: bool = False, indent: int = 0, icon: str = ""):
        """Print a tree-style item"""
        prefix = "└─" if is_last else "├─"
        icon_str = f"{icon} " if icon else ""
        spacing = "   " * indent
        console.print(f"{spacing}[dim]{prefix}[/dim] {icon_str}{text}")

    @staticmethod
    def print_code_block(
        code: str,
        language: str = "python",
        theme: str = "monokai",
        line_numbers: bool = True,
    ):
        """Print code with syntax highlighting and customization"""
        syntax = Syntax(code, language, theme=theme, line_numbers=line_numbers, word_wrap=True)
        console.print(syntax)

    @staticmethod
    def print_panel(content: str, title: str = "", style: str = "cyan", border_style: str = "blue"):
        """Print content in a styled panel"""
        panel = Panel(
            content,
            title=title,
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def print_table(data: List[Dict[str, Any]], title: Optional[str] = None):
        """Print data in a styled table"""
        if not data:
            return

        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")

        # Add columns from first row
        for key in data[0].keys():
            table.add_column(key.replace("_", " ").title(), style="white")

        # Add rows
        for row in data:
            table.add_row(*[str(v) for v in row.values()])

        console.print(table)

    @staticmethod
    def create_welcome_panel():
        """Create an enhanced welcome panel with ASCII art header"""
        welcome_text = Text()

        ascii_art = r"""
      _ _                           _       _ _
     | (_)                         (_)     (_) |
   __| |_  __ _ _ __   __ _  ___    _ _ __  _| |_
  / _` | |/ _` | '_ \ / _` |/ _ \  | | '_ \| | __|
 | (_| | | (_| | | | | (_| | (_) | | | | | | | |_
  \__,_| |\__,_|_| |_|\__, |\___/  |_|_| |_|_|\__|
      _/ |             __/ |
     |__/             |___/
"""

        welcome_text.append(ascii_art, style=UIColors.ACCENT)
        welcome_text.append("\n  Django Project Setup Tool\n", style="bold white")
        welcome_text.append(
            "  Create production-ready Django projects with modern architecture\n\n",
            style=UIColors.MUTED,
        )
        welcome_text.append("  Repository: ", style=UIColors.MUTED)
        welcome_text.append("https://github.com/S4NKALP/djinit\n", style="blue underline")
        welcome_text.append("  License: MIT\n", style=UIColors.MUTED)

        return welcome_text

    @staticmethod
    def create_summary_panel(
        project_dir: str,
        project_name: str,
        app_names: List[str],
        success: bool,
        duration: Optional[float] = None,
    ):
        """Create a clean completion summary with optional duration"""
        console.print("\n")

        if success:
            # Success header
            console.print(f"[bold green]{'═' * 70}[/bold green]")
            console.print(f"[bold green]{f'{Icons.PARTY} SETUP COMPLETE! {Icons.PARTY}'.center(70)}[/bold green]")
            console.print(f"[bold green]{'═' * 70}[/bold green]\n")

            # Duration if provided
            if duration:
                console.print(f"[dim]{Icons.CLOCK} Completed in {duration:.2f} seconds[/dim]\n")

            # Project details
            console.print(f"[bold cyan]{Icons.TARGET} Project Details:[/bold cyan]")
            console.print("   [dim]│[/dim]")
            console.print(f"   [dim]├─[/dim] [bold]Directory:[/bold] [white]{project_dir}[/white]")
            console.print(f"   [dim]├─[/dim] [bold]Project:[/bold] [white]{project_name}[/white]")
            console.print(f"   [dim]└─[/dim] [bold]Apps:[/bold] [white]{', '.join(app_names)}[/white]")
            console.print()

            # Next steps
            console.print(f"[bold cyan]{Icons.ROCKET} Next Steps:[/bold cyan]")
            console.print("   [dim]│[/dim]")
            console.print("   [dim]├─[/dim] [dim]1.[/dim] Navigate to your project directory")
            console.print("   [dim]├─[/dim] [dim]2.[/dim] Set environment variables in .env file")
            console.print("   [dim]├─[/dim] [dim]3.[/dim] Run migrations: [cyan]python manage.py migrate[/cyan]")
            console.print(
                "   [dim]├─[/dim] [dim]4.[/dim] Create superuser: [cyan]python manage.py createsuperuser[/cyan]"
            )
            console.print("   [dim]└─[/dim] [dim]5.[/dim] Start server: [cyan]python manage.py runserver[/cyan]")
            console.print()

            # Useful URLs
            console.print(f"[bold cyan]{Icons.LINK} Useful URLs:[/bold cyan]")
            console.print("   [dim]│[/dim]")
            console.print("   [dim]├─[/dim] Admin: [blue]http://localhost:8000/admin/[/blue]")
            console.print("   [dim]├─[/dim] API Docs: [blue]http://localhost:8000/docs/[/blue]")
            console.print("   [dim]└─[/dim] API Schema: [blue]http://localhost:8000/schema/[/blue]")
            console.print()

            console.print(f"[bold green]{'═' * 70}[/bold green]\n")

        else:
            # Error header
            console.print(f"[bold red]{'═' * 70}[/bold red]")
            console.print(f"[bold red]{'❌ SETUP FAILED'.center(70)}[/bold red]")
            console.print(f"[bold red]{'═' * 70}[/bold red]\n")

            console.print("[red]The setup process encountered an error.[/red]\n")

            # Troubleshooting
            console.print(f"[bold yellow]{Icons.MAGNIFIER} Troubleshooting Tips:[/bold yellow]")
            console.print("   [dim]│[/dim]")
            console.print("   [dim]├─[/dim] Check the error messages above")
            console.print("   [dim]├─[/dim] Ensure you have write permissions")
            console.print("   [dim]├─[/dim] Verify Django is installed correctly")
            console.print("   [dim]└─[/dim] Try running with elevated permissions")
            console.print()

            console.print(f"[bold red]{'═' * 70}[/bold red]\n")

    @staticmethod
    def create_progress_display(description: str = "Processing", total_steps: int = 100):
        """Create a comprehensive live progress display"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        return progress

    @staticmethod
    @contextmanager
    def status(message: str, spinner: str = "dots"):
        """Context manager for status display with spinner"""
        with console.status(f"[bold cyan]{message}...", spinner=spinner):
            yield

    @staticmethod
    def confirm(prompt: str, default: bool = True) -> bool:
        """Display a confirmation prompt"""
        default_str = "Y/n" if default else "y/N"
        response = console.input(f"[bold cyan]?[/bold cyan] {prompt} [{default_str}]: ").strip().lower()

        if not response:
            return default
        return response in ("y", "yes")

    @staticmethod
    def prompt(message: str, default: Optional[str] = None) -> str:
        """Display an input prompt with optional default"""
        if default:
            message = f"{message} [{default}]"
        response = console.input(f"[bold cyan]?[/bold cyan] {message}: ").strip()
        return response or default or ""

    @staticmethod
    def print_command(command: str, description: Optional[str] = None):
        """Print a command with optional description"""
        console.print(f"[{UIColors.CODE}]$ {command}[/{UIColors.CODE}]")
        if description:
            console.print(f"[dim]  {description}[/dim]")


class ProgressTracker:
    """Enhanced progress tracking with context"""

    def __init__(self, total_steps: int, description: str = "Setup Progress"):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self.task = None
        self.total_steps = total_steps
        self.description = description
        self.current_step = 0

    def __enter__(self):
        self.progress.start()
        self.task = self.progress.add_task(self.description, total=self.total_steps)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()

    def update(self, advance: int = 1, description: Optional[str] = None):
        """Update progress with optional description"""
        if description:
            self.progress.update(self.task, advance=advance, description=description)
        else:
            self.progress.update(self.task, advance=advance)
        self.current_step += advance

    def set_description(self, description: str):
        """Update the progress description"""
        self.progress.update(self.task, description=description)
