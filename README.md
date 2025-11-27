# djinit

<div align="center">

> PyPI didn't allow the original name, so you'll find it as **djinitx** on PyPI

<img src="https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white" alt="PyPI">
<img src="https://img.shields.io/badge/Django-4.2%20%7C%205.1%20%7C%205.2-0C4B33?logo=django&logoColor=white" alt="Django">
<img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python">
<a href="https://github.com/S4NKALP/djinit/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>

</div>

**djinit** helps you set up a production-ready Django project in minutes. No more copy-pasting settings or manually wiring up apps, just answer a few questions and get a modern Django project with REST API, authentication, documentation, and deployment configs ready to go.

## Why djinit?

Starting a Django project usually means spending hours setting up the same things: splitting settings for dev/prod, configuring DRF, adding JWT auth, setting up CORS, preparing for deployment. djinit does all of this for you with sensible defaults and lets you choose the project structure that fits your needs.

## Installation

**Recommended** (using pipx):

```bash
pipx install djinitx
```

Or with pip:

```bash
pip install djinitx
```

Or with uv:

```bash
uv tool install djinitx
```

**Requirements**: Python 3.13+

## Getting Started

Just run:

```bash
djinit setup
```

You can also use the shorter alias:

```bash
dj setup
```

The tool will ask you a few questions:

1. **What structure do you want?**
   - **Standard**: Classic Django layout with split settings
   - **Predefined**: Organized with `apps/` and `api/` folders (great for larger projects)
   - **Unified**: Everything under `core/` and `apps/` (clean and minimal)
   - **Single Folder**: All apps in one configurable folder (simple and flat)

2. **Project Setup**:
   - Where to create it (use `.` for current directory)
   - Project name (or directory name for Single Folder)

3. **Database Configuration**:
   - Use `DATABASE_URL` (cleaner, recommended)
   - Or separate DB variables
   - Choose between PostgreSQL or MySQL

4. **Django Apps** (Standard Structure only):
   - Whether to use an `apps/` folder
   - Which apps to create

5. **CI/CD Pipeline**:
   - GitHub Actions, GitLab CI, both, or skip it

That's it! Your project will be ready with everything configured.

## What You Get

Every project includes:

- **Split settings** for development and production
- **Django REST Framework** with JWT authentication
- **API documentation** (Swagger UI at `/docs/`)
- **CORS** configured for local development
- **WhiteNoise** for serving static files
- **PostgreSQL** support (SQLite for dev)
- **Modern admin** interface (django-jazzmin)
- **Deployment ready** with Procfile and runtime.txt
- **Development tools** (Justfile with common commands)
- **Environment template** (.env.sample)
- **Git ready** (.gitignore included)

## Commands

### Create a Project

```bash
djinit setup
```

### Add Apps to Existing Project

```bash
djinit app users products orders
```

This automatically creates the apps, adds them to `INSTALLED_APPS`, and wires up URLs.

### Generate Secret Keys

```bash
djinit secret
```

Need more? Use `--count 5` or change length with `--length 64`.

## Project Structures

### Standard Structure

The classic Django layout with split settings:

```
myproject/
├── manage.py
├── myproject/          # Config module
│   ├── settings/       # Split settings
│   ├── urls.py
│   └── wsgi.py
└── apps/               # Your apps (optional)
    └── users/
```

### Single Folder Layout

Simple structure with all apps in one folder:

```
myproject/
├── manage.py
├── project/            # Configurable folder name
│   ├── settings/
│   ├── urls.py
│   ├── models/         # All models here
│   ├── api/            # API views and serializers
│   │   └── your_model_name/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   └── wsgi.py
```

### Predefined Structure

Organized for larger projects:

```
myproject/
├── manage.py
├── config/             # Django config
│   ├── settings/
│   └── urls.py
├── apps/               # Business logic
│   ├── users/
│   └── core/
└── api/                # API routes
    └── v1/
```

### Unified Structure

Clean and minimal:

```
myproject/
├── manage.py
├── core/               # Django config
│   ├── settings/
│   └── urls.py
└── apps/               # Main application package
    ├── admin/
    ├── models/
    ├── serializers/
    ├── views/
    ├── urls/
    └── api/            # API routes
```

## Development Workflow

Your project comes with a `Justfile` for common tasks:

```bash
just dev              # Start dev server
just migrate          # Run migrations
just makemigrations   # Create migrations
just shell            # Django shell
just test             # Run tests
just format           # Format code
just lint             # Lint code
```

Don't have `just` installed? No problem—these are just shortcuts for standard Django commands.

## What's Included

### Packages

- Django (web framework)
- Django REST Framework (API)
- djangorestframework-simplejwt (JWT auth)
- drf-spectacular (API docs)
- django-cors-headers (CORS)
- django-jazzmin (modern admin)
- whitenoise (static files)
- psycopg2-binary (PostgreSQL)
- gunicorn (production server)
- python-dotenv (environment variables)

### API Endpoints

- `/admin/` - Django admin
- `/token/` - Get JWT token
- `/token/refresh/` - Refresh token
- `/docs/` - Swagger UI (dev only)
- `/schema/` - OpenAPI schema (dev only)

### Settings

**Development**: SQLite, debug mode, console emails, permissive CORS
**Production**: PostgreSQL, security hardened, SMTP emails, strict CORS

## Environment Setup

Copy `.env.sample` to `.env` and fill in your values:

```bash
SECRET_KEY=your-secret-key-here  # Use: djinit secret
DATABASE_URL=postgres://user:pass@host:5432/db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

For development, SQLite works out of the box—no database setup needed!

## Contributing

Found a bug or have an idea? Open an issue or submit a pull request. Contributions are always welcome!

## License

MIT © Sankalp Tharu
