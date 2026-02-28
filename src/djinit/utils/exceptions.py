"""
Custom exceptions for djinit.
"""


class DjinitError(Exception):
    """Base exception for all djinit errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ConfigError(DjinitError):
    """Raised when there is a configuration or metadata error."""

    pass


class FileError(DjinitError):
    """Raised when a file operation fails."""

    pass


class TemplateError(DjinitError):
    """Raised when template rendering fails."""

    pass
