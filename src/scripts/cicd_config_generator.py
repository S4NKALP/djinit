"""
CI/CD pipeline manager for djinit
Handles creation of Github Actions and GitLab CI onfigurations
"""

import os

from src.scripts.template_engine import template_engine
from src.utils import change_cwd, create_file_with_content


class CICDConfigGenerator:
    def __init__(self, project_root: str, project_name: str):
        self.project_root = project_root
        self.project_name = project_name

    def create_github_actions(self) -> bool:
        with change_cwd(self.project_root):
            github_dir = os.path.join(self.project_root, ".github", "workflows")
            os.makedirs(github_dir, exist_ok=True)

        context = {"project_name": self.project_name}
        workflow_content = template_engine.render_template("github_actions_ci.j2", context)
        workflow_file = os.path.join(github_dir, "ci.yml")
        create_file_with_content(
            workflow_file,
            workflow_content,
            f"Created Github Actions workflow ({workflow_file})",
        )
        return True

    def create_gitlab_ci(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            gitlab_ci_content = template_engine.render_template("gitlab_ci.j2", context)
            config_file = ".gitlab-ci.yml"
            create_file_with_content(
                config_file,
                gitlab_ci_content,
                f"Created GitLab CI configuration ({config_file})",
            )
            return True
