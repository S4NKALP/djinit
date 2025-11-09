# djinit

<div align="center">

> PyPI did not allow the original name, so the package is released as **djinitx**

<img src="https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white" alt="PyPI">
<img src="https://img.shields.io/badge/Django-4.2%20%7C%205.1%20%7C%205.2-0C4B33?logo=django&logoColor=white" alt="Django">
<img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python">
<a href="https://github.com/S4NKALP/djinit/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>

</div>

A fast, interactive CLI to bootstrap a modern, production‑ready Django project in minutes — featuring split settings, DRF and JWT integration, OpenAPI docs, CORS, static file handling via WhiteNoise, Postgres‑friendly configuration, CI/CD templates, deployment helpers, and battle‑tested defaults that deliver a polished developer experience out of the box.

## Features

- ✨ **Split settings**: `settings/base.py`, `settings/development.py`, `settings/production.py`
- 🏗️ **Three structure types**: Standard Django layout, Predefined structure, or Unified structure
- 🧱 **Flexible app layout**: Flat or nested apps package (e.g., `apps/`)
- 🧩 **Complete app scaffolding**: URLs, serializers, routes, views, models, admin, tests
- 🔗 **Auto-wired URLs**: Project URLs automatically include your apps
- 🧰 **Essential utility files**: `.gitignore`, `README.md`, `.env.sample`, `requirements.txt`, `pyproject.toml`
- 🚀 **Deployment helpers**: `Justfile`, `Procfile`, `runtime.txt`
- 🛠️ **CI/CD templates**: GitHub Actions and/or GitLab CI workflows
- 🔐 **Secret key generator**: Generate secure Django secret keys
- 🎨 **Polished UX**: Beautiful interactive interface with `rich` library
- 📦 **App management**: Add apps to existing projects with automatic settings configuration

## Installation

Using pipx (recommended):

```bash
pipx install djinitx
```

Using pip:

```bash
pip install djinitx
```

Using uv:

```bash
uv tool install djinitx
```

From source:

```bash
git clone https://github.com/S4NKALP/djinit
cd djinit
pip install -e .
```

**Requirements**: Python 3.13+

## Quick Start

Run the interactive setup:

```bash
djinit setup
# or
dj setup
```

The interactive setup will guide you through:

1. **Structure Type Selection**:
   - Standard structure (default Django layout)
   - Predefined structure (`apps/users`, `apps/core`, `api/` layout)
   - Unified structure (`core/`, `apps/core`, `apps/api` layout)

2. **Project Configuration**:
   - Project directory (or use current directory with `.`)
   - Django project name (used for the config module)
   - Apps layout (flat vs nested package like `apps/`)
   - App names (comma‑separated)

3. **CI/CD Configuration**:
   - GitHub Actions only
   - GitLab CI only
   - Both (GitHub Actions + GitLab CI)
   - None (skip CI/CD)

4. **Database Configuration**:
   - Use `DATABASE_URL` (recommended for production)
   - Use individual database parameters

## Commands

### Setup Command

Launch the interactive project generator:

```bash
djinit setup
# or
dj setup
```

### App Command

Create one or more Django apps in an existing project:

```bash
djinit app <names>
# or
dj app <names>
```

**Examples**:

- `djinit app users` or `dj app users`
- `djinit app users,products,orders` or `dj app users,products,orders`
- `djinit app users products orders` or `dj app users products orders`

The app command automatically:

- Creates the app with all necessary files
- Adds the app to `INSTALLED_APPS` in `settings/base.py`
- Configures URLs if using predefined structure
- Detects and respects your project's structure (nested/flat)

### Secret Command

Generate secure Django `SECRET_KEY` values:

```bash
djinit secret [--count N] [--length L]
# or
dj secret [--count N] [--length L]
```

**Examples**:

- `djinit secret` - Generate 3 keys with default length (50)
- `djinit secret --count 5 --length 50` - Generate 5 keys of length 50
- `dj secret --count 10 --length 64` - Generate 10 keys of length 64

## Project Structure Types

### Standard Structure

The default Django layout with split settings:

```
project_name/
├── manage.py
├── project_name/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/              # Optional nested apps
│   └── <app_name>/
│       ├── urls.py
│       ├── serializers.py
│       ├── routes.py
│       └── ...
└── <app_name>/        # Or flat apps
    └── ...
```

### Predefined Structure

A production-ready structure with `apps/` and `api/` packages:

```
project_name/
├── manage.py
├── config/             # Django config module
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
├── apps/
│   ├── users/          # Pre-configured users app
│   │   ├── models/
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── services/
│   │   └── tests/
│   └── core/           # Core utilities
│       ├── exceptions.py
│       ├── utils/
│       ├── mixins/
│       └── middleware/
└── api/
    ├── urls.py
    └── v1/
        └── urls.py
```

### Unified Structure

A unified structure with `core/` as the main module:

```
project_name/
├── manage.py
├── core/               # Main Django config
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── core/           # Core app with models, utils
    │   ├── models/
    │   └── utils/
    └── api/            # API app
        └── ...
```

## What Gets Generated

### Core Files

- **Django project structure** with split settings
- **Settings package**: `base.py`, `development.py`, `production.py`
- **Project URLs**: Auto-configured with app includes
- **WSGI/ASGI**: Production-ready application entry points
- **manage.py**: Django management script

### App Files

Each app includes:

- `urls.py` - URL routing
- `serializers.py` - DRF serializers
- `routes.py` - API route definitions
- `views.py` - View classes
- `models.py` - Database models
- `admin.py` - Admin configuration
- `tests.py` - Test structure
- `apps.py` - App configuration
- `migrations/` - Migration directory

### Utility Files

- `.gitignore` - Comprehensive Python/Django gitignore
- `README.md` - Project documentation template
- `.env.sample` - Environment variables template (includes `SECRET_KEY` placeholder, `DATABASE_URL` or individual DB params, email settings)
- `requirements.txt` - All necessary dependencies
- `pyproject.toml` - Modern Python project configuration (includes ruff linting/formatting config)
- `Justfile` - Development commands (migrations, server, etc.) using `uv run`
- `Procfile` - PaaS deployment configuration (Heroku, Railway, Render, etc.) with release task for migrations
- `runtime.txt` - Python version specification

### CI/CD Files

- `.github/workflows/ci.yml` - GitHub Actions workflow (if selected)
- `.gitlab-ci.yml` - GitLab CI configuration (if selected)

## Included Packages

The generated `requirements.txt` includes:

- **Django** - Web framework
- **python-dotenv** - Environment variable management
- **django-jazzmin** - Modern Django admin interface
- **djangorestframework** - REST API framework
- **djangorestframework_simplejwt** - JWT authentication (note: underscore in package name)
- **drf-spectacular** - OpenAPI 3.0 schema generation
- **django-cors-headers** - CORS handling
- **whitenoise** - Static file serving for production
- **psycopg2-binary** - PostgreSQL adapter
- **gunicorn** - Production WSGI server
- **dj-database-url** - Database URL parsing (when using `DATABASE_URL`)

This gives you a complete stack with:

- REST API with DRF
- JWT authentication endpoints: `/token/`, `/token/refresh/`, `/token/blacklist/`
- OpenAPI documentation at `/docs/` and `/schema/` (available in DEBUG mode only)
- CORS support (configured for localhost:3000 in development)
- Production-ready static file handling with WhiteNoise
- PostgreSQL support (SQLite in development by default)

## Environment and Database

### Environment Variables

A `.env.sample` file is generated with:

- `DJANGO_SETTINGS_MODULE` - Settings module path
- `SECRET_KEY` - Placeholder for your secret key (use `djinit secret` to generate)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- Database configuration (either `DATABASE_URL` or individual `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)
- Email settings (SMTP configuration)

### Database Configuration

**Development (Default)**

- Uses SQLite (`db.sqlite3`) for local development
- No database configuration needed

**Production**

**Option 1: DATABASE_URL (Recommended)**

If you opt into `DATABASE_URL`, the production settings use `dj-database-url`:

```
DATABASE_URL=postgres://user:password@host:port/database
```

**Option 2: Individual Parameters**

Traditional Django database configuration with separate environment variables:

- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port

## Development Workflow

After setup, use the generated `Justfile` for common tasks (uses `uv` by default):

```bash
just dev              # Start development server (uv run python manage.py runserver)
just migrate          # Run migrations
just makemigrations   # Create migrations
just shell            # Django shell
just test             # Run tests
just format           # Format code with ruff
just lint             # Lint code with ruff
just setup            # Complete setup (uv sync + migrate + createsuperuser)
just server           # Start production server with gunicorn
```

**Note**: The Justfile uses `uv run` for all commands. If you're not using `uv`, you can modify the Justfile or use Django commands directly.

### API Endpoints

The generated project includes:

- **Admin**: `/admin/`
- **JWT Authentication**:
  - `/token/` - Obtain access token
  - `/token/refresh/` - Refresh access token
  - `/token/blacklist/` - Blacklist refresh token
- **API Documentation** (DEBUG mode only):
  - `/docs/` - Swagger UI
  - `/schema/` - OpenAPI schema

### Settings Configuration

- **Base Settings** (`settings/base.py`):
  - DRF configuration with JWT authentication
  - CORS settings
  - WhiteNoise for static files
  - Security headers
  - Pagination (20 items per page)

- **Development Settings** (`settings/development.py`):
  - SQLite database
  - DEBUG = True
  - Console email backend
  - CORS allows all origins
  - Generated secret key (replace in production)

- **Production Settings** (`settings/production.py`):
  - PostgreSQL database (via `DATABASE_URL` or individual params)
  - DEBUG = False
  - Security settings (HTTPS redirect, HSTS, secure cookies)
  - SMTP email configuration
  - Secret key from environment variable

## Contributing

Contributions are welcome! Please:

1. Open an issue for bugs or feature ideas
2. Fork the repository
3. Create a feature branch
4. Submit a pull request with a clear description

## Acknowledgments

- Django and the Django community
- Jinja2 - Template engine
- rich - Beautiful terminal output
- click - CLI framework
- ruff - Fast Python linter and formatter

## License

MIT © Sankalp Tharu
