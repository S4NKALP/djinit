"""
Deployment file generator for djinit.
Handles creation of Justfile, Procfile, and deployment-related files.
"""

from src.scripts.template_engine import template_engine
from src.utils import change_cwd, create_file_with_content


class DeploymentConfigGenerator:
    def __init__(self, project_root: str, project_name: str):
        self.project_root = project_root
        self.project_name = project_name

    def create_justfile(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            justfile_content = template_engine.render_template("justfile.j2", context)
            create_file_with_content(
                "justfile",
                justfile_content,
                "Created justfile with Django development tasks",
            )
        return True

    def create_procfile(self) -> bool:
        with change_cwd(self.project_root):
            context = {"project_name": self.project_name}
            procfile_content = template_engine.render_template("procfile.j2", context)
            create_file_with_content(
                "Procfile",
                procfile_content,
                "Created Procfile with Gunicorn configuration",
            )
        return True

    def create_gunicorn_config(self) -> bool:
        with change_cwd(self.project_root):
            gunicorn_config_content = f"""# Gunicorn configuration file for {self.project_name}
# Usage: gunicorn -c gunicorn_config.py {self.project_name}.wsgi:application

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "{self.project_name}"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
"""

            create_file_with_content(
                "gunicorn_config.py",
                gunicorn_config_content,
                f"Created gunicorn_config.py with Gunicorn configuration",
            )
        return True

    def create_runtime_txt(self, python_version: str = "3.13") -> bool:
        with change_cwd(self.project_root):
            context = {"python_version": python_version}
            runtime_content = template_engine.render_template("runtime_txt.j2", context)
            create_file_with_content(
                "runtime.txt",
                runtime_content,
                f"Created runtime.txt with Python version specification",
            )
        return True

    def create_nixpacks_toml(self) -> bool:
        with change_cwd(self.project_root):
            nixpacks_content = f"""# Nixpacks configuration for {self.project_name}
# Used by Railway, Render, and other platforms that support Nixpacks

[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install --upgrade pip", "pip install -r requirements.txt"]

[phases.build]
cmds = ["python manage.py collectstatic --noinput"]

[start]
cmd = "gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:$PORT"
"""

            create_file_with_content(
                "nixpacks.toml",
                nixpacks_content,
                f"Created nixpacks.toml for Nixpacks deployment",
            )
        return True
