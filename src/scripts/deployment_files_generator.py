"""
Deployment files generator for djinit
Handles creation of Justfile, Procfile, and deployment-related files.
"""

from scr.utils import change_cwd, create_file_with_content


class DeploymentFileGenerator:
    def __init__(self, project_root: str, project_name: str):
        self.project_root = project_root
        self.project_name = project_name

    def create_justfile(self) -> bool:
        with change_cwd(self.project_root):
            justfile_content = f"""# Justfile for {self.project_name}
# Task runner for Django development
# Install just: https://github.com/casey/just

# Default task: show available commands
default:
    @just --list

# Run development server
dev:
    uv run python manage.py runserver

# Run development server with custom host and port
dev-server HOST="0.0.0.0" PORT="8000":
    uv run python manage.py runserver {{{{HOST}}}}:{{{{PORT}}}}

# Create migrations for all apps
makemigrations:
    uv run python manage.py makemigrations

# Create migrations for specific app
makemigrations-app APP:
    uv run python manage.py makemigrations {{{{APP}}}}

# Run all migrations
migrate:
    uv run python manage.py migrate

# Reset database (delete all migrations)
reset-db:
    uv run python manage.py flush --noinput
    uv run python manage.py migrate

# Create superuser
createsuperuser:
    uv run python manage.py createsuperuser

# Collect static files
collectstatic:
    uv run python manage.py collectstatic --noinput

# Run Django shell
shell:
    uv run python manage.py shell

# Run Django shell plus (IPython)
shell-plus:
    uv run python manage.py shell_plus

# Run tests
test:
    uv run python manage.py test

# Run tests with coverage
test-coverage:
    uv run pytest --cov=. --cov-report=html --cov-report=term

# Lint code with ruff
lint:
    uv run ruff check .

# Format code with ruff
format:
    uv run ruff format .

# Lint and format code
style:
    uv run ruff check .
    uv run ruff format .

# Check security issues
check:
    uv run python manage.py check

# Check security issues (production settings)
check-deploy:
    uv run python manage.py check --deploy

# Show all database migrations status
showmigrations:
    uv run python manage.py showmigrations

# Sync dependencies (uv equivalent of pip freeze)
requirements:
    uv pip compile

# Run all linting and checks
ci:
    uv run ruff check .
    uv run ruff format --check .
    uv run python manage.py check

# Start interactive shell
shell-ipython:
    uv run python manage.py shell_plus

# Clear all cache
clear-cache:
    uv run python manage.py clear_cache

# Show Django version
version:
    uv run python manage.py version

# Run database shell
dbshell:
    uv run python manage.py dbshell

# Start production server with gunicorn
server:
    uv run gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:8000

# Start production server with gunicorn workers
server-prod WORKERS="4":
    uv run gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:8000 --workers {{{{WORKERS}}}}

# Start production server with gunicorn and reload on file changes
server-watch:
    uv run gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:8000 --reload

# Clean Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {{}} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name ".coverage" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {{}} +
    rm -rf htmlcov/
    rm -rf .pytest_cache/

# Setup project for development (using uv)
setup:
    uv sync
    uv run python manage.py migrate
    uv run python manage.py createsuperuser

# Complete setup including static files
setup-complete:
    uv sync
    uv run python manage.py migrate
    uv run python manage.py collectstatic --noinput
    uv run python manage.py createsuperuser

# Install a new package
install PACKAGE:
    uv add {{{{PACKAGE}}}}

# Install a dev package
install-dev PACKAGE:
    uv add --dev {{{{PACKAGE}}}}

# Remove a package
remove PACKAGE:
    uv remove {{{{PACKAGE}}}}
"""

            result = create_file_with_content(
                "justfile",
                justfile_content,
                "Created justfile with Django development tasks",
            )
            return result

    def create_procfile(self) -> bool:
        with change_cwd(self.project_root):
            procfile_content = f"""# Procfile for {self.project_name}
# Used for deploying to PaaS platforms like Heroku, Railway, Render, etc.

# Web server process (using Gunicorn)
# Adjust workers based on your needs: (2 x CPU cores) + 1
web: gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - --log-level info

# Alternative web server configurations (uncomment to use):
# web: gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120
# web: gunicorn {self.project_name}.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --worker-class gevent --worker-connections 1000 --timeout 120

# Release task (runs migrations before deployment)
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

# Uncomment below to run scheduled tasks (if using Celery)
# worker: celery -A {self.project_name} worker --loglevel=info
# beat: celery -A {self.project_name} beat --loglevel=info

# Development server (for local testing with Foreman/Overmind)
# web: python manage.py runserver 0.0.0.0:$PORT
"""

            result = create_file_with_content(
                "Procfile",
                procfile_content,
                "Created Procfile with Gunicorn configuration",
            )
            return result

    def create_gunicorn_config(self) -> bool:
        """Create a gunicorn configuration file."""
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

            config_file = "gunicorn_config.py"
            result = create_file_with_content(
                config_file,
                gunicorn_config_content,
                f"Created {config_file} with Gunicorn configuration",
            )
            return result

    def create_runtime_txt(self, python_version: str = "3.13") -> bool:
        """Create runtime.txt file for specifying Python version."""
        with change_cwd(self.project_root):
            runtime_content = f"""python-{python_version}
"""
            runtime_file = "runtime.txt"
            result = create_file_with_content(
                runtime_file,
                runtime_content,
                f"Created {runtime_file} with Python version specification",
            )
            return result

    def create_nixpacks_toml(self) -> bool:
        """Create nixpacks.toml for Nixpacks deployment configuration."""
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

            config_file = "nixpacks.toml"
            result = create_file_with_content(
                config_file,
                nixpacks_content,
                f"Created {config_file} for Nixpacks deployment",
            )
            return result
