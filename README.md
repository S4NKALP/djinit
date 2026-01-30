# djinit

<div align="center">

> PyPI didn't allow the original name, so you'll find it as **djinitx** on PyPI

<img src="https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white" alt="PyPI">
<img src="https://img.shields.io/badge/Django-4.2%20%7C%205.1%20%7C%205.2-0C4B33?logo=django&logoColor=white" alt="Django">
<img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python">
<a href="https://github.com/S4NKALP/djinit/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>

</div>

**djinit** helps you set up a production‑ready Django project in minutes. No more copy‑pasting settings or manually wiring up apps—just answer a few questions and get a modern Django project with REST API, authentication, documentation, and deployment configs ready to go.

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

**Requirements**: Python 3.13+

## Getting Started

```bash
djinit setup
```

or the shorter alias:

```bash
dj setup
```

The wizard will ask you a few questions:

1. **What structure do you want?**
   - **Standard** – Classic Django layout with split settings
   - **Predefined** – Organized with `apps/` and `api/` folders (great for larger projects)
   - **Unified** – Everything under `core/` and `apps/` (clean and minimal)
   - **Single Folder** – All apps in one configurable folder (simple and flat)

2. **Project Setup** – Destination directory (use `.` for current) and project name.

3. **Database Configuration** – Choose `DATABASE_URL` (recommended) or individual variables; pick PostgreSQL or MySQL.

4. **Django Apps** *(Standard structure only)* – Whether to create an `apps/` folder and which apps to scaffold.

5. **CI/CD Pipeline** – GitHub Actions, GitLab CI, both, or skip it.

That’s it—your project will be ready with everything configured.

## What You Get

- **Split settings** for development and production
- **Django REST Framework** with JWT authentication
- **API documentation** (Swagger UI at `/docs/`)
- **CORS** configured for local development
- **WhiteNoise** for static files
- **PostgreSQL** support (SQLite for dev)
- **Modern admin** interface (`django-jazzmin`)
- **Deployment ready** with `Procfile` and `runtime.txt`
- **Development tools** (`Justfile` with common commands)
- **Environment template** (`.env.sample`)
- **Git ready** (`.gitignore` included)

## Commands

### Create a Project

```bash
djinit setup
```

### Add Apps to an Existing Project

```bash
djinit app users products orders
```

Creates the apps, adds them to `INSTALLED_APPS`, and wires up URLs.

### Generate Secret Keys

```bash
djinit secret
```

Use `--count 5` to generate five keys or `--length 64` to change the length.

## Project Structures

### Standard Structure

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

```
myproject/
├── manage.py
├── project/            # Configurable folder name
│   ├── settings/
│   ├── urls.py
│   ├── models/         # All models here
│   ├── api/            # API views & serializers
│   │   └── your_model_name/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   └── wsgi.py
```

### Predefined Structure

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

Your project ships with a `Justfile` for common tasks:

```bash
just dev              # Start dev server
just migrate          # Run migrations
just makemigrations   # Create migrations
just shell            # Django shell
just test             # Run tests
just format           # Format code
just lint             # Lint code
```

If you don’t have `just` installed, these are just shortcuts for the equivalent Django commands.

## What's Included

### Packages

- **Django** – Web framework
- **Django REST Framework** – API toolkit
- **djangorestframework‑simplejwt** – JWT authentication
- **drf‑spectacular** – OpenAPI/Swagger docs
- **django‑cors‑headers** – CORS handling
- **django‑jazzmin** – Modern admin UI
- **whitenoise** – Static file serving
- **psycopg2‑binary** – PostgreSQL driver
- **gunicorn** – Production WSGI server
- **python‑dotenv** – `.env` handling

### API Endpoints

| Endpoint          | Description                     |
|-------------------|---------------------------------|
| `/admin/`         | Django admin                    |
| `/token/`         | Obtain JWT token                |
| `/token/refresh/` | Refresh JWT token               |
| `/docs/`          | Swagger UI (dev only)           |
| `/schema/`        | OpenAPI schema (dev only)       |

### Settings Overview

- **Development** – SQLite, `DEBUG=True`, console email backend, permissive CORS.
- **Production** – PostgreSQL, hardened security settings, SMTP email backend, strict CORS.

## Environment Setup

Copy the sample file and fill in your values:

```bash
cp .env.sample .env
```

```dotenv
SECRET_KEY=your-secret-key-here  # Generate with: djinit secret
DATABASE_URL=postgres://user:pass@host:5432/db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

SQLite works out of the box for development—no extra DB setup required.

## Roadmap

The following items are tracked in **TODO.md** and represent the near‑future direction of djinit.

### Planned Features
- **Docker Support** – Auto‑generate a `Dockerfile` for containerized deployments.
- **Frontend Integration** – Scaffold React, Vue, or HTMX alongside the Django backend.
- **Celery Integration** – Simplify background task setup with Celery.
- **More Packages** – Add optional integrations for popular Django packages.

### Enhancements
- **Add more project structure templates** – Expand the set of ready‑made layouts.
- **Add testing framework setup** – Provide pytest and coverage configuration out of the box.
- **Fix bugs** – Ongoing maintenance and bug resolution.

### Completed
- **Interactive configuration wizard** – Streamlined project creation experience.
- **Improved structure detection** – Smarter detection of existing Django layouts.

> Contributions that address any of the above items are highly welcome!

## Contributing

Found a bug or have an idea? Open an issue or submit a pull request. Contributions are always welcome!

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Make your changes and ensure tests pass (`just test`).
4. Submit a pull request with a clear description of the change.

Please follow the existing code style (ruff + black) and include tests for new functionality.

## License

MIT © Sankalp Tharu

---

*© 2024 Sankalp Tharu. All rights reserved.*
