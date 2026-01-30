"""
Secret key generation command.
"""

from rich.panel import Panel
from rich.text import Text

from djinit.core.base import BaseCommand
from djinit.ui.console import UIColors, UIFormatter, console
from djinit.utils.secretkey import display_secret_keys, generate_multiple_keys


class SecretCommand(BaseCommand):
    """Command to generate Django secret keys."""

    def execute(self) -> None:
        count = getattr(self.args, "count", 3)
        length = getattr(self.args, "length", 50)

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
