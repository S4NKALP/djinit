# djinit (djinitx)

> **Note**: Published as **[djinitx](https://pypi.org/project/djinitx/)** on PyPI.

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white)](https://pypi.org/project/djinitx/)
[![Django versions](https://img.shields.io/badge/Django-4.2%20%7C%205.1%20%7C%205.2%20%7C%206.0-0C4B33?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python versions](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/S4NKALP/djinit/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

A modern, production-grade CLI project generator for Django. `djinit` scaffolds robust Django projects with modular architecture presets, Django REST Framework, JWT authentication, OpenAPI docs, deployment configurations, frontend integrations, and architecture-aware app scaffolding through an intuitive interactive wizard.

```bash
# Quick install & run
pipx install djinitx
djinit setup
```

---

## Table of Contents

- [Installation](#installation)
- [CLI Commands](#cli-commands)
  - [`djinit setup` / `dj setup`](#djinit-setup--dj-setup)
  - [`djinit app`](#djinit-app-architecture-aware)
  - [`djinit secret`](#djinit-secret)
- [Architecture Presets](#architecture-presets)
  - [Overview Table](#architecture-overview)
  - [Simple Layouts](#simple-layouts)
  - [Application Presets](#application-presets)
  - [Advanced Presets](#advanced-presets)
- [Production Base Models](#production-base-models)
- [Project Manifest (`.djinit.toml`)](#project-manifest-djinittoml)
- [Frontend Integrations](#frontend-integrations)
- [Deployment Ready](#deployment-ready)
- [Development Workflow](#development-workflow)
- [API Endpoints](#api-endpoints)
- [Contributing & License](#contributing)

---

## Installation

```bash
# Recommended (isolated global environment via pipx)
pipx install djinitx

# Or via uv tool
uv tool install djinitx

# Or inside a virtualenv via pip / uv
pip install djinitx
# or
uv pip install djinitx
```

*Requires Python 3.11+.*

---

## CLI Commands

### `djinit setup` / `dj setup`

Starts the interactive configuration wizard:

```bash
djinit setup
# or use the short alias
dj setup
```

The interactive wizard walks you through:

1. **Architecture preset**: Categorized into **Simple**, **Application**, and **Advanced**.
2. **Project name & directory**: Select target path or current directory.
3. **Database selection**: PostgreSQL, MySQL, or SQLite3 (with automatic `DATABASE_URL` or local path setup).
4. **Frontend stack**: Clean selection of Tailwind CSS, HTMX, Alpine.js, Vite, or pure Django templates.
5. **App initialization**: Add your core domain apps automatically.
6. **CI/CD configuration**: GitHub Actions, GitLab CI, both, or none.

### `djinit app` (Architecture-Aware)

Generate one or multiple Django apps that automatically match your active project's architecture:

```bash
# Single app
djinit app accounts

# Multiple apps in one invocation
djinit app products orders billing
```

**Architecture-aware capabilities:**
- Reads project architecture from `.djinit.toml` (with backward compatibility for `.djinit` JSON).
- Places files in the correct directory (`apps/<app>` vs root).
- Configures full `AppConfig` paths in `USER_DEFINED_APPS` in `settings/base.py`.
- Generates architecture-specific layers:
  - **Modular Monolith**: `models/`, `services/`, `selectors/`, `views/`, `api/`, `tests/`
  - **Service Layer**: `models.py`, `services.py`, `selectors.py`, `forms.py`, `views.py`, `api/`, `tests/`
  - **Full-Stack HTMX**: `views/`, `forms.py`, `urls.py`, and `templates/<app>/` with partial templates
  - **DDD**: `domain/`, `application/`, `infrastructure/`, and `presentation/`
  - **Clean Architecture**: `domain/`, `use_cases/`, `interfaces/`, and `infrastructure/`
  - **Multi-Tenant**: Tenant-scoped models, tenant services, and isolation unit tests
- Safely and idempotently wires up URL includes in `config/urls.py`.

### `djinit secret`

Generate cryptographically secure Django `SECRET_KEY` tokens:

```bash
# Generate 3 keys of 50 characters (default)
djinit secret

# Generate custom count and length
djinit secret --count 5 --length 64
```

### `djinit template` (Export & Custom Starters)

Export any existing Django project into a reusable, sanitized custom starter template:

```bash
# Launch interactive export wizard (prompts for directory, name, description & confirmation)
djinit template export

# Or export directly with options
djinit template export . --name my-custom-starter --description "Company SaaS Starter"

# List all saved custom templates
djinit template list

# Create a new project directly from your custom template
djinit template apply my-custom-starter --name new_saas_app --dir ./new_saas_app

# Or use the --template flag during setup
djinit setup --template my-custom-starter --name new_saas_app

# Delete a custom template
djinit template delete my-custom-starter --force
```

**Custom template sanitization features:**
- Automatically ignores `.venv/`, `venv/`, `__pycache__/`, `.git/`, `node_modules/`, `db.sqlite3`, and build artifacts.
- Masks sensitive secrets and `SECRET_KEY` in settings.
- Converts `.env` into a sanitized `.env.sample` and generates a cryptographically fresh `SECRET_KEY` upon instantiation.
- Automatically parameterizes internal project package names (`[[ project_name ]]`).

---

## Architecture Presets

### Architecture Overview

| Preset | Category | Best For | App Structure |
|---|---|---|---|
| **Standard** | Simple | Classical Django applications | Flat app root or nested `apps/` |
| **Single Folder** | Simple | Single-package projects | Everything inside `{module_name}/` |
| **Lightweight** | Simple | Micro-services, prototypes, MVPs | Minimal Django, zero boilerplate |
| **Predefined** | Application | Dedicated REST APIs | Dedicated `api/v1/` and `apps/` |
| **Unified** | Application | Shared application root | `core/` config with unified `apps/` |
| **Modular Monolith** | Application | ERP, CRM, LMS, enterprise business systems | Packaged submodules (`services/`, `selectors/`) |
| **Service Layer** | Application | Medium-to-large business applications | Explicit separation of read/write logic |
| **Full-Stack HTMX** | Application | Interactive server-rendered SPAs | Templates, HTMX partials, Alpine.js |
| **Domain-Driven Design** | Advanced | Complex enterprise domains | `domain/`, `application/`, `infrastructure/` |
| **Clean Architecture** | Advanced | Layered software with strict inversion of control | `domain/`, `use_cases/`, `interfaces/` |
| **Multi-Tenant** | Advanced | B2B SaaS with organization data isolation | Shared-schema, `TenantMiddleware`, scoped queries |

---

### Simple Layouts

#### 1. Standard

Classic Django layout with split environments:

```text
myproject/
├── manage.py
├── myproject/          # Configuration module
│   ├── settings/       # base.py, development.py, production.py
│   ├── urls.py
│   └── wsgi.py
├── shared/             # Reusable base models & utilities
└── apps/               # Business logic applications
    └── users/
```

#### 2. Lightweight

Minimal, fast-bootstrapping Django preset without unnecessary overhead:

```text
myproject/
├── manage.py
├── config/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
└── templates/
    └── home.html
```

---

### Application Presets

#### 1. Modular Monolith

Enterprise-scale modular structure designed for large development teams and clear bounded contexts:

```text
myproject/
├── manage.py
├── config/             # Settings (base, development, production, testing)
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── accounts/       # Independent domain module
│       ├── models/     # Model package discoverable by migrations
│       │   ├── __init__.py
│       │   └── item.py
│       ├── services/   # Business writes & atomic transactions
│       ├── selectors/  # Optimized read queries
│       ├── views/      # HTTP request handling
│       ├── api/        # DRF serializers & viewsets
│       ├── tests/      # Domain unit tests
│       ├── apps.py
│       └── urls.py
├── common/             # Reusable kernel across modules
│   ├── db/             # Base models & querysets
│   ├── middleware/     # Request ID & logging middleware
│   ├── permissions/    # Object & role permissions
│   └── utils/
└── pyproject.toml
```

#### 2. Service Layer

Separates state invariants, database queries, and business workflows cleanly:

```text
apps/
└── billing/
    ├── models.py       # Persistence & model invariants
    ├── services.py     # Business operations (writes & mutations)
    ├── selectors.py    # Read queries & database lookups
    ├── forms.py        # Django forms & validation
    ├── views.py        # HTTP controllers
    ├── api/            # Serializers & viewsets
    ├── tests/
    └── apps.py
```

#### 3. Full-Stack HTMX

Modern interactive user experiences without Node.js or heavy client frameworks:

```text
myproject/
├── templates/
│   ├── layouts/
│   │   └── base.html   # Tailwind CSS + HTMX + Alpine.js shell
│   ├── components/     # Navbars, modals, alerts
│   └── includes/       # Toasts and messages
├── apps/
│   └── dashboard/
│       ├── views/      # Full-page and request.htmx partial views
│       ├── forms.py
│       ├── urls.py
│       └── templates/dashboard/
│           ├── index.html
│           └── partials/item_row.html
└── static/
```

---

### Advanced Presets

#### 1. Domain-Driven Design (DDD)

Strict separation between business entities and framework persistence:

```text
apps/
└── orders/
    ├── domain/         # Pure Python entities & value objects
    │   ├── entity.py
    │   └── value_objects.py
    ├── application/    # Use cases, commands, and DTOs
    │   └── use_cases.py
    ├── infrastructure/ # Django ORM models & repository adapters
    │   ├── models/
    │   └── repository.py
    ├── presentation/   # Views, serializers, and endpoints
    │   ├── views.py
    │   └── urls.py
    └── apps.py
```

#### 2. Clean Architecture

Hexagonal / Ports-and-Adapters structure prioritizing dependency inversion:

```text
apps/
└── delivery/
    ├── domain/         # Enterprise business rules
    ├── use_cases/      # Application-specific business rules
    ├── interfaces/     # Repository interfaces & gateway contracts
    ├── infrastructure/ # Django ORM persistence & external clients
    └── apps.py
```

#### 3. Multi-Tenant (Shared-Schema)

Native tenant isolation for B2B SaaS applications:

```text
myproject/
├── tenancy/            # Tenancy core module
│   ├── models.py       # Tenant, TenantMembership, TenantAwareModel
│   ├── middleware.py   # TenantMiddleware (resolves UUID or slug header)
│   └── apps.py
└── apps/
    └── inventory/
        ├── models.py   # Models inherit TenantAwareModel
        ├── services.py # Scoped to current tenant
        ├── tests/
        │   └── test_isolation.py  # Verifies cross-tenant data isolation
        └── apps.py
```

---

## Production Base Models

Every generated project includes ready-to-use abstract base models in `shared/base.py` (or `common/db/models.py`):

```python
from shared import (
    BaseModel,  # UUIDModel + TimeStampedModel
    TimeStampedModel,  # created_at (indexed), updated_at
    UUIDModel,  # id = UUIDField(primary_key=True)
    OrderedModel,  # sort_order, is_active
    ActivatableModel,  # is_active flag
    SluggedModel,  # slug = SlugField(unique=True)
    SoftDeleteModel,  # Soft-delete support with .delete(), .restore(), .hard_delete()
)


class Product(SoftDeleteModel, BaseModel):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### Soft-Delete Features:
- `.delete()`: Sets `deleted_at = timezone.now()` and `is_deleted = True`.
- `.restore()`: Clears `deleted_at` and restores the record.
- `.hard_delete()`: Permanently deletes the database row.
- `.objects`: Default manager automatically filters active records (`.alive()`).
- `.all_objects`: QuerySet manager accessing both active and soft-deleted records.

---

## Project Manifest (`.djinit.toml`)

Projects created with `djinit` include a `.djinit.toml` manifest file, enabling architecture detection across CLI commands:

```toml
# Generated by djinit
[project]
name = "myproject"
structure = "modular_monolith"
schema_version = 1
apps_dir = "apps"
module_name = "config"

[features]
drf = true
jwt = true
htmx = false
tailwind = true
alpine = false
vite = false

[database]
engine = "postgresql"
use_database_url = true

[deployment]
target = "docker"
```

---

## Frontend Integrations

Customize your frontend during project setup:

| Tool | Integration | Features |
|---|---|---|
| **Tailwind CSS** | `django-tailwind-cli` | Zero-Node CLI executable, DaisyUI components preconfigured |
| **HTMX** | `django-htmx` | `HtmxMiddleware`, `request.htmx` partial view support |
| **Alpine.js** | Standalone Script | Lightweight client-side UI interactivity (tabs, modals, transitions) |
| **Vite** | `django-vite` | Fast HMR asset bundler for React, Vue, Svelte, and TypeScript |

---

## Deployment Ready

Every generated project ships with production deployment assets:

- **Docker Compose (`docker-compose.yml`)**: Multi-container setup orchestrating the Django web service and PostgreSQL / MySQL / SQLite volume storage.
- **cPanel & Shared Hosting (`passenger_wsgi.py`)**: Out-of-the-box WSGI configuration for Apache Phusion Passenger environments.
- **Containerization (`Dockerfile`)**: Production container image with security best practices and non-root user.
- **Static Asset Delivery (`whitenoise`)**: Gzip and Brotli asset compression for direct production serving.
- **Production WSGI Server (`gunicorn`)**: Preconfigured for high-throughput concurrency.

---

## Development Workflow

Generated projects come pre-configured with a `Justfile` for common development tasks:

```bash
just dev              # Start Django development server
just migrate          # Apply database migrations
just makemigrations   # Create new migrations
just test             # Run test suite
just lint             # Lint with ruff
just format           # Format with ruff
just vite             # Start Vite asset server (if selected)
```

*(If `just` is not installed, standard `python manage.py` commands work out of the box).*

---

## API Endpoints

Every API-enabled project includes preconfigured authentication and documentation routes:

| Route | Provider | Description |
|---|---|---|
| `/admin/` | `django-jazzmin` | Modern, responsive Django administration panel |
| `/token/` | `rest_framework_simplejwt` | Obtain JWT access and refresh token pair |
| `/token/refresh/` | `rest_framework_simplejwt` | Refresh expired access tokens |
| `/docs/` | `drf-yasg` | Interactive Swagger UI API documentation |
| `/schema/` | `drf-yasg` | ReDoc API specification viewer |

---

## Contributing

Contributions, feedback, and pull requests are warmly welcome!

1. Fork the repository on GitHub.
2. Create a feature branch (`git checkout -b feat/my-improvement`).
3. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/).
4. Verify with `uv run pytest` and `uv run ruff check .`.
5. Open a Pull Request.

---

## License

Distributed under the [MIT License](https://github.com/S4NKALP/djinit/blob/main/LICENSE).

Copyright © 2026 [Sankalp Tharu](https://sankalptharu.com.np).
