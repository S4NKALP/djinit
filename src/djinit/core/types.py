"""
Core data structures and types for djinit.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ProjectMetadata:
    package_name: str
    use_github_actions: bool = False
    use_gitlab_ci: bool = False
    nested_apps: bool = False
    nested_dir: str | None = None
    use_database_url: bool = False
    database_type: str = "postgresql"
    predefined_structure: bool = False
    unified_structure: bool = False
    single_structure: bool = False
    project_module_name: str | None = None

    def to_dict(self) -> dict:
        return {
            "package_name": self.package_name,
            "use_github_actions": self.use_github_actions,
            "use_gitlab_ci": self.use_gitlab_ci,
            "nested_apps": self.nested_apps,
            "nested_dir": self.nested_dir,
            "use_database_url": self.use_database_url,
            "database_type": self.database_type,
            "predefined_structure": self.predefined_structure,
            "unified_structure": self.unified_structure,
            "single_structure": self.single_structure,
            "project_module_name": self.project_module_name,
        }


@dataclass
class ProjectSetup:
    project_dir: str
    project_name: str
    primary_app: str
    app_names: list[str]
    metadata: ProjectMetadata

    def to_tuple(self) -> Tuple[str, str, str, list, dict]:
        return (self.project_dir, self.project_name, self.primary_app, self.app_names, self.metadata.to_dict())
