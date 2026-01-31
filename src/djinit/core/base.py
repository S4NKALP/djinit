"""
Base classes for the djinit architecture.
Defines the common interface for services, commands, and utilities.
"""

from abc import abstractmethod
from typing import Any


class BaseObject:
    """
    Base object for all djinit classes.
    """

    def __init__(self, *args, **kwargs):
        pass


class BaseService(BaseObject):
    """
    Base class for all services.
    Services handle business logic and orchestration.
    """

    def __init__(self, project_root: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_root = project_root


class BaseCommand(BaseObject):
    """
    Base class for all CLI commands.
    Commands handle user input and invoke services.
    """

    def __init__(self, args: Any, *args_list, **kwargs):
        super().__init__(*args_list, **kwargs)
        self.args = args

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass


class BaseUtils(BaseObject):
    """
    Base class for utility collections.
    Utilities provide helper functions.
    """

    pass
