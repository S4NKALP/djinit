"""
Core data structures and types for djinit.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Tuple


class AuthProvider(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"


def auth_context(metadata: dict) -> dict:
    providers = metadata.get("auth_providers", [])
    return {"auth_providers": providers, "auth_api": bool(providers and metadata.get("auth_api"))}


def auth_app_labels(providers: list[str], auth_api: bool) -> set[str]:
    if not providers:
        return set()
    labels = {"allauth", "account", "socialaccount", *providers}
    if auth_api:
        labels.add("headless")
    return labels


@dataclass
class ProjectMetadata:
    package_name: str
    use_github_actions: bool = False
    use_gitlab_ci: bool = False
    nested_apps: bool = False
    nested_dir: str | None = None
    use_database_url: bool = False
    database_type: str = "postgresql"
    use_tailwind: bool = False
    use_htmx: bool = False
    use_vite: bool = False
    predefined_structure: bool = False
    unified_structure: bool = False
    single_structure: bool = False
    project_module_name: str | None = None
    architecture: str | None = None
    use_alpine: bool = False
    use_drf: bool = True
    use_jwt: bool = True
    deployment_target: str = "docker"
    auth_providers: list[str] = field(default_factory=list)
    auth_api: bool = False
    use_celery: bool = False
    use_redis_cache: bool = False

    def to_dict(self) -> dict:
        return {
            "package_name": self.package_name,
            "use_github_actions": self.use_github_actions,
            "use_gitlab_ci": self.use_gitlab_ci,
            "nested_apps": self.nested_apps,
            "nested_dir": self.nested_dir,
            "use_database_url": self.use_database_url,
            "database_type": self.database_type,
            "use_tailwind": self.use_tailwind,
            "use_htmx": self.use_htmx,
            "use_vite": self.use_vite,
            "predefined_structure": self.predefined_structure,
            "unified_structure": self.unified_structure,
            "single_structure": self.single_structure,
            "project_module_name": self.project_module_name,
            "architecture": self.architecture,
            "use_alpine": self.use_alpine,
            "use_drf": self.use_drf,
            "use_jwt": self.use_jwt,
            "deployment_target": self.deployment_target,
            "auth_providers": self.auth_providers,
            "auth_api": bool(self.auth_providers and self.auth_api),
            "use_celery": self.use_celery,
            "use_redis_cache": self.use_redis_cache,
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
