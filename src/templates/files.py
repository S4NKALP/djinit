"""
File management utilities for djinit.
Handles creation and modification of project files.
"""

import os

from src.utils import change_cwd, create_file_with_content


class FileManager:
    def __init__(self, project_root: str, project_name: str, app_names: list):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.project_configs = os.path.join(project_root, project_name)
        self.settings_folder = os.path.join(self.project_configs, "settings")
        self.settings_file = os.path.join(self.project_configs, "settings.py")

    def create_gitignore(self) -> bool:
        with change_cwd(self.project_root):
            gitignore_content = [
                "# Python",
                "*.py[cod]",
                "*$py.class",
                "*.so",
                "__pycache__/",
                "*.egg-info/",
                "dist/",
                "build/",
                ".eggs/",
                "*.egg",
                "# Django",
                "*.log",
                "local_settings.py",
                "db.sqlite3",
                "db.sqlite3-journal",
                "*.sqlite3",
                "# Environment",
                ".env",
                ".venv",
                "env/",
                "venv/",
                "ENV/",
                "env.bak/",
                "venv.bak/",
                "# IDEs",
                ".vscode/",
                ".idea/",
                "*.swp",
                "*.swo",
                "*~",
                ".project",
                ".pydevproject",
                ".settings/",
                ".ropeproject/",
                "# OS",
                ".DS_Store",
                "*.DS_Store",
                "Thumbs.db",
                "desktop.ini",
                "# Django specific",
                "media/",
                "staticfiles/",
                "staticfiles/",
                "static_root/",
                "/static/",
                "# Testing",
                ".coverage",
                "htmlcov/",
                ".pytest_cache/",
                ".tox/",
                "coverage.xml",
                "*.cover",
                ".hypothesis/",
                ".cache",
                "# Logs",
                "logs/",
                "*.log",
                "npm-debug.log*",
                "yarn-debug.log*",
                "yarn-error.log*",
                "# Node modules (if using frontend tools)",
                "node_modules/",
                "# Secret keys",
                "secret.txt",
                "secrets.json",
                "# Jupyter Notebook",
                ".ipynb_checkpoints",
                "# Backup files",
                "*.bak",
                "*.tmp",
                "*~",
                "# Database",
                "*.db",
                "*.sql",
                "# Cloud",
                ".cloud",
            ]

            return create_file_with_content(
                ".gitignore",
                "\n".join(gitignore_content) + "\n",
                "Created .gitignore file",
            )

    def create_requirements(self) -> bool:
        with change_cwd(self.project_root):
            requirements = [
                "Django>=5.2.7",
                "python-dotenv>=1.1.1",
                "django-jazzmin>=3.0.1",
                "djangorestframework>=3.16.1",
                "djangorestframework_simplejwt>=5.5.1",
                "drf-spectacular>=0.28.0",
                "django-cors-headers>=4.9.0",
                "whitenoise>=6.8.2",
                "psycopg2-binary>=2.9.9",  # For PostgreSQL support
                "gunicorn>=21.2.0",  # For production deployment
            ]

            return create_file_with_content(
                "requirements.txt",
                "\n".join(requirements) + "\n",
                "Created requirements.txt with Django dependencies",
            )

    def create_readme(self) -> bool:
        with change_cwd(self.project_root):
            readme_content = f"""# {self.project_name}

A Django project created with django-setup.

## Features

- Modern project structure with environment-specific settings
- Pre-configured REST API with JWT authentication
- Essential dependencies and utilities
- Production-ready configuration

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables in `.env` file

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. Start development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
{self.project_name}/
├── {self.project_name}/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
{"".join([f"├── {app}/\n" for app in self.app_names])}├── manage.py
├── requirements.txt
├── pyproject.toml
├── .env.sample
└── README.md
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs/
- Schema: http://localhost:8000/schema/
"""

            return create_file_with_content(
                "README.md",
                readme_content,
                "Created README.md file",
            )

    def create_env_file(self) -> bool:
        """Create .env.sample file with environment variables."""
        with change_cwd(self.project_root):
            env_content = f"""# Django settings
DJANGO_SETTINGS_MODULE={self.project_name}.settings.development
SECRET_KEY= your-secret-key
ALLOWED_HOSTS=api.your-domain.com,www.your-domain.com

# Database
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
"""

            return create_file_with_content(
                ".env.sample",
                env_content,
                "Created .env.sample file with generated secret key",
            )

    def create_pyproject_toml(self, metadata: dict) -> bool:
        with change_cwd(self.project_root):
            pyproject_content = f"""[project]
name = "{metadata["package_name"]}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.13"
license = {{ text = "MIT }}
dependencies = [
    "django>=5.2.7",
    "python-dotenv>=1.1.1",
    "django-jazzmin>=3.0.1",
    "djangorestframework>=3.16.1",
    "djangorestframework-simplejwt>=5.5.1",
    "drf-spectacular>=0.28.0",
    "django-cors-headers>=4.9.0",
    "whitenoise>=6.8.2",
    "psycopg2-binary>=2.9.9",
    "gunicorn>=21.2.0",
]

[tool.ruff]
line-length = 88
target-version = "py38"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by formatter
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.lint.isort]
known-first-party = ["{self.project_name}"]
"""

            return create_file_with_content(
                "pyproject.toml",
                pyproject_content,
                "Created pyproject.toml file for uv",
            )

    def create_app_urls(self) -> bool:
        for app_name in self.app_names:
            app_path = os.path.join(self.project_root, app_name)
            with change_cwd(app_path):
                urls_content = f"""from django.urls import path
from . import views

app_name = '{app_name}'

urlpatterns = [
    # Add your URL patterns here
    # path('', views.index, name='index'),
]
"""

                create_file_with_content(
                    "urls.py",
                    urls_content,
                    f"Created {app_name}/urls.py",
                    should_format=True,
                )
        return True

    def update_project_urls(self) -> bool:
        with change_cwd(self.project_configs):
            # Generate URL includes for all apps
            app_urls = "\n    ".join([f'path("", include("{app_name}.urls")),' for app_name in self.app_names])

            urls_content = f"""from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT tokens
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    # App URLs
    {app_urls}
]

# Don't show schema in production
if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    ]
"""

            result = create_file_with_content(
                "urls.py",
                urls_content,
                "Updated project urls.py with comprehensive URL configuration",
                should_format=True,
            )
            return result

    def update_wsgi_file(self) -> bool:
        with change_cwd(self.project_configs):
            wsgi_content = """import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE"))

application = get_wsgi_application()
"""

            return create_file_with_content(
                "wsgi.py",
                wsgi_content,
                "Updated wsgi.py with custom configuration",
                should_format=True,
            )

    def update_asgi_file(self) -> bool:
        with change_cwd(self.project_configs):
            asgi_content = """import os
from dotenv import load_dotenv
from django.core.asgi import get_asgi_application

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE"))

application = get_asgi_application()
"""

            return create_file_with_content(
                "asgi.py",
                asgi_content,
                "Updated asgi.py with custom configuration",
                should_format=True,
            )

    def update_manage_py(self) -> bool:
        """Update manage.py with custom configuration."""
        with change_cwd(self.project_root):
            manage_content = """#!/usr/bin/env python
\"\"\"Django's command-line utility for administrative tasks.\"\"\"
import os
import sys
from dotenv import load_dotenv


def main():
    \"\"\"Run administrative tasks.\"\"\"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    load_dotenv()
    main()
"""

            return create_file_with_content(
                "manage.py",
                manage_content,
                "Updated manage.py with custom configuration",
                should_format=True,
            )
