from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from djinit.creators.files import FileCreator


class ArchitectureHandler:
    """Base class for architecture handlers."""

    @classmethod
    def scaffold_project(cls, file_creator: FileCreator) -> None:
        raise NotImplementedError

    @classmethod
    def scaffold_app(cls, app_name: str, apps_dir: str) -> bool:
        raise NotImplementedError
