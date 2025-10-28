"""
Shared file utility functions.
Contains common file operations used across multiple managers.
"""

import subprocess

from src.scripts.console import UIFormatter


def format_file(filename: str) -> None:
    """Format Python file using Ruff formatter."""
    subprocess.run(["ruff", "format", filename], check=False, capture_output=True)


def create_file_with_content(
    filename: str, content: str, success_message: str, should_format: bool = False
) -> bool:
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
