"""
Django Secret Key Generator

Generate secure Django secret keys for different environments.
"""

import secrets
import string

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from djinit.scripts.console_ui import UIColors

console = Console()


def generate_secret_key(length: int = 50) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_multiple_keys(count: int = 3, length: int = 50) -> list[str]:
    return [generate_secret_key(length) for _ in range(count)]


def display_secret_keys(keys: list[str]) -> None:
    table = Table(title="🔐 Django Secret Keys", show_header=True, header_style="bold blue")
    table.add_column("Environment", style="cyan", no_wrap=True)
    table.add_column("Secret Key", style="dim")

    for i, key in enumerate(keys, 1):
        table.add_row(f"Environment {i}", key)

    console.print(table)
    console.print()


def generate_secret_command():
    keys = generate_multiple_keys(3, 50)
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


if __name__ == "__main__":
    generate_secret_command()
