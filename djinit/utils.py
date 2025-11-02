"""
Shared utility functions.
Contains common operations used across multiple managers.
"""

import os
import subprocess
import sys
from contextlib import contextmanager

from djinit.scripts.console_ui import UIFormatter


def format_file(filename: str) -> None:
    """Format Python file using Ruff formatter."""
    # Use 'python -m ruff' instead of 'ruff' for better compatibility
    subprocess.run([sys.executable, "-m", "ruff", "format", filename], check=False, capture_output=True)


def create_file_with_content(filename: str, content: str, success_message: str, should_format: bool = False) -> bool:
    """
    Create a file with content, optionally format it, and print success message.

    Args:
        filename: Name of the file to create
        content: Content to write to the file
        success_message: Message to print on success
        should_format: Whether to format the file with ruff

    Returns:
        True if successful
    """
    with open(filename, "w") as file:
        file.write(content)

    if should_format:
        format_file(filename)

    UIFormatter.print_success(success_message)
    return True


@contextmanager
def change_cwd(path: str):
    """Temporarily change the current working directory.

    Ensures the original directory is restored even if an exception occurs.
    """
    original_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_cwd)
