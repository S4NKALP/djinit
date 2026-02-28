"""
Django Secret Key Generator

Generate secure Django secret keys for different environments.
"""

import secrets
import string

from rich.console import Console
from rich.table import Table

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


if __name__ == "__main__":
    keys = generate_multiple_keys(3, 50)
    display_secret_keys(keys)
