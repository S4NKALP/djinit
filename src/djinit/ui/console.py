"""
Console UI utilities for djinit.
Provides clean, minimal styling and user interface components.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import questionary
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


class UIColors:
    """Color scheme for consistent UI styling"""

    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold blue"
    HIGHLIGHT = "bold cyan"
    MUTED = "dim white"
    ACCENT = "bold magenta"
    CODE = "bold white"


class Icons:
    """Minimal icon set"""

    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    ROCKET = "🚀"
    TARGET = "🎯"
    LINK = "🔗"
    CLOCK = "⏱"
    PARTY = "🎉"


class UIFormatter:
    """Utility class for consistent UI formatting"""

    @staticmethod
    def print_success(message: str, icon: str = Icons.SUCCESS):
        """Print success message"""
        console.print(f"[{UIColors.SUCCESS}]{icon}[/{UIColors.SUCCESS}] [bold]{message}[/bold]")

    @staticmethod
    def print_error(message: str, icon: str = Icons.ERROR, details: Optional[str] = None):
        """Print error message with optional details"""
        console.print(f"[{UIColors.ERROR}]{icon}[/{UIColors.ERROR}] [bold]{message}[/bold]")
        if details:
            console.print(f"   [dim]{details}[/dim]")

    @staticmethod
    def print_warning(message: str, icon: str = Icons.WARNING):
        """Print warning message"""
        console.print(f"[{UIColors.WARNING}]{icon}[/{UIColors.WARNING}] [bold]{message}[/bold]")

    @staticmethod
    def print_info(message: str, icon: str = ""):
        """Print info message"""
        if icon:
            console.print(f"[{UIColors.INFO}]{icon}[/{UIColors.INFO}] [bold]{message}[/bold]")
        else:
            console.print(f"[{UIColors.INFO}]{message}[/{UIColors.INFO}]")

    @staticmethod
    def create_live_progress(description: str = "Setup Progress", total_steps: int = 100):
        """Create a live progress display"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            console=console,
        )
        task = progress.add_task(description, total=total_steps)
        return progress, task

    @staticmethod
    def print_header(text: str, style: str = UIColors.ACCENT):
        """Print a styled header"""
        console.print(f"\n[{style}]{'═' * 70}[/{style}]")
        console.print(f"[{style}]{text.center(70)}[/{style}]")
        console.print(f"[{style}]{'═' * 70}[/{style}]\n")

    @staticmethod
    def print_separator(char: str = "─", width: int = 70, style: str = UIColors.MUTED):
        """Print a visual separator"""
        console.print(f"[{style}]{char * width}[/{style}]")

    @staticmethod
    def print_panel(content: str, title: str = "", border_style: str = "blue"):
        """Print content in a styled panel"""
        panel = Panel(content, title=title, border_style=border_style, box=box.ROUNDED, padding=(1, 2))
        console.print(panel)

    @staticmethod
    def print_table(data: List[Dict[str, Any]], title: Optional[str] = None):
        """Print data in a styled table"""
        if not data:
            return

        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")

        for key in data[0].keys():
            table.add_column(key.replace("_", " ").title(), style="white")

        for row in data:
            table.add_row(*[str(v) for v in row.values()])

        console.print(table)

    @staticmethod
    def create_welcome_panel():
        """Create a minimal welcome panel"""
        welcome_text = Text()

        welcome_text.append("\n  ╔═══════════════════════════════════════╗\n", style=UIColors.ACCENT)
        welcome_text.append("  ║         Django Init (djinit)          ║\n", style=UIColors.ACCENT)
        welcome_text.append("  ╚═══════════════════════════════════════╝\n\n", style=UIColors.ACCENT)
        welcome_text.append("  Create production-ready Django projects\n\n", style=UIColors.MUTED)
        welcome_text.append("  Repository: ", style=UIColors.MUTED)
        welcome_text.append("https://github.com/S4NKALP/djinit\n", style="blue underline")

        return welcome_text

    @staticmethod
    def create_summary_panel(
        project_dir: str,
        project_name: str,
        app_names: List[str],
        success: bool,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create a minimal completion summary"""
        if success:
            console.print("\n")
            console.print(f"[bold green]{'═' * 70}[/bold green]")
            console.print(f"[bold green]{f'{Icons.PARTY} SETUP COMPLETE'.center(70)}[/bold green]")
            console.print(f"[bold green]{'═' * 70}[/bold green]\n")
        else:
            console.print("\n")
            console.print(f"[bold red]{'═' * 70}[/bold red]")
            console.print(f"[bold red]{'❌ SETUP FAILED'.center(70)}[/bold red]")
            console.print(f"[bold red]{'═' * 70}[/bold red]\n")
            console.print("[red]Setup encountered an error. Check messages above.[/red]\n")
            console.print(f"[bold red]{'═' * 70}[/bold red]\n")

    @staticmethod
    @contextmanager
    def status(message: str, spinner: str = "dots"):
        """Context manager for status display"""
        with console.status(f"[bold cyan]{message}...", spinner=spinner):
            yield

    @staticmethod
    def confirm(prompt: str, default: bool = True) -> bool:
        """Display a confirmation prompt as a selectable list"""
        choices = [
            questionary.Choice("Yes", value=True),
            questionary.Choice("No", value=False),
        ]
        default_choice = choices[0] if default else choices[1]

        result = questionary.select(
            prompt,
            choices=choices,
            default=default_choice,
        ).ask()

        if result is None:
            raise KeyboardInterrupt

        return result

    @staticmethod
    def prompt(message: str, default: Optional[str] = None) -> str:
        """Display an input prompt"""
        return questionary.text(message, default=default or "").ask()

    @staticmethod
    def handle_exception(e: Exception):
        """Handle and display exceptions gracefully"""
        from djinit.utils.exceptions import DjinitError

        if isinstance(e, DjinitError):
            UIFormatter.print_error(e.message, details=e.details)
        else:
            console.print("\n")
            console.print(f"[bold red]{'═' * 70}[/bold red]")
            console.print(f"[bold red]{'💥 UNEXPECTED ERROR'.center(70)}[/bold red]")
            console.print(f"[bold red]{'═' * 70}[/bold red]\n")
            console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")
            console.print("[dim]Please report this issue on GitHub.[/dim]\n")
            # Optionally print traceback for debugging if needed, or log it
            # console.print_exception()
