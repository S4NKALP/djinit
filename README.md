# djinit

> PyPI didn't allow the original name, so you'll find it as **djinitx** on PyPI

<div align="center">

<img src="https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white" alt="PyPI">
<img src="https://img.shields.io/badge/Django-5.1%20%7C%205.2%20%7C%206.0-0C4B33?logo=django&logoColor=white" alt="Django">
<img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python">
<a href="https://github.com/S4NKALP/djinit/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>

</div>

A CLI that scaffolds production-ready Django projects with DRF, JWT auth, API docs, and deployment configs - all through an interactive wizard. No more copy-pasting settings or wiring up apps by hand.

```bash
pipx install djinitx
djinit setup
```

## Installation

```bash
# Recommended - isolated environment
pipx install djinitx

# Or with uv
uv tool install djinitx

# Or with pip
pip install djinitx
```

Requires Python 3.13+.

## Usage

### Create a project

```bash
djinit setup
# or
dj setup
```

The wizard walks you through these choices:

1. **Project structure & architecture**:
   - **Simple**: Standard, Single Folder, Lightweight
   - **Application**: Predefined, Unified, Modular Monolith, Service Layer, Full-Stack HTMX
   - **Advanced**: Domain-Driven Design (DDD), Clean Architecture, Multi-Tenant
2. **Project name and directory**
3. **Database** - PostgreSQL, MySQL, or SQLite3; `DATABASE_URL` or individual env vars
4. **Frontend tools** - Tailwind CSS, DaisyUI, HTMX, Alpine.js, and/or Vite (optional)
5. **Django apps** - Name them; optionally nest under an `apps/` package
6. **CI/CD** - GitHub Actions, GitLab CI, both, or none

When you're done, you have a fully configured Django project ready to run.

### Architecture-Aware `djinit app`

```bash
djinit app accounts
djinit app products orders
```

The `djinit app` command detects your project architecture via `.djinit.toml` and generates apps matching your architecture conventions:
- **Modular Monolith**: creates `models/`, `services/`, `selectors/`, `views/`, `api/`, `tests/`, and `urls.py`.
- **Service Layer**: creates `models.py`, `services.py`, `selectors.py`, `forms.py`, `views.py`, `api/`, and `tests/`.
- **Full-Stack HTMX**: creates `views/`, `forms.py`, `urls.py`, and `templates/<app>/` with HTMX partials.
- **Domain-Driven Design (DDD)**: creates `domain/`, `application/`, `infrastructure/`, and `presentation/` layers.
- **Clean Architecture**: creates `domain/`, `use_cases/`, `interfaces/`, and `infrastructure/` layers.
- **Multi-Tenant**: creates tenant-isolated models and services extending `tenancy.models.TenantAwareModel`.

Apps are registered automatically in `USER_DEFINED_APPS` in `settings/base.py` with fully-qualified `AppConfig` paths and wired up safely to URL routing.

### Generate secret keys

```bash
djinit secret
djinit secret --count 5 --length 64
```

## What You Get

Every project ships with:

- **Split settings** - `base.py`, `development.py`, `production.py` with sensible defaults
- **Django REST Framework** - With JWT authentication (access + refresh tokens)
- **API documentation** - Swagger UI at `/docs/`, ReDoc at `/schema/`
- **CORS** - Configured for local dev, locked down for production
- **WhiteNoise** - Static file serving, production-ready
- **django-jazzmin** - Modern admin interface
- **Environment management** - `.env.sample` with `django-environ`
- **Deployment configs** - `Dockerfile`, `Procfile`, `runtime.txt`
- **CI/CD pipelines** - GitHub Actions and/or GitLab CI
- **Task runner** - `Justfile` with common commands
- **`.gitignore`** - Python + Node defaults

Optional add-ons when selected:

| Feature | Package | What's configured |
|---|---|---|
| Tailwind CSS | django-tailwind-cli | Settings, DaisyUI theme, Node install in Docker |
| HTMX | django-htmx | Installed app + HtmxMiddleware |
| Vite | django-vite | `vite.config.ts`, dev/prod mode toggles, CI build step |

### Development workflow

```bash
just dev              # Start dev server
just migrate          # Run migrations
just test             # Run tests
just lint             # Lint with ruff
just format           # Format with ruff
just vite             # Start Vite dev server (if selected)
just dev-full         # Django + Vite together (if selected)
```

No `just` installed? These map directly to Django management commands.

## Project Structures

### Standard

```
myproject/
├── manage.py
├── myproject/          # Config module
│   ├── settings/       # base.py, development.py, production.py
│   ├── urls.py
│   └── wsgi.py
└── apps/               # Your apps (optional)
    └── users/
```

### Predefined

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

### Unified

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
    └── api/
```

### Single Folder

```
myproject/
├── manage.py
├── project/            # Configurable name
│   ├── settings/
│   ├── urls.py
│   ├── models/
│   ├── api/
│   └── wsgi.py
```

### Modular Monolith

```
myproject/
├── manage.py
├── config/             # Settings (base, development, production, testing)
├── apps/
│   ├── accounts/       # Independent business domain module
│   │   ├── models/
│   │   ├── services/
│   │   ├── selectors/
│   │   ├── views/
│   │   ├── api/
│   │   ├── tests/
│   │   └── urls.py
│   └── core/
├── common/             # Reusable kernel (db, middleware, permissions, utils)
└── tests/
```

### Service Layer

```
apps/
└── products/
    ├── models.py       # Persistence & constraints
    ├── services.py     # Business operations & atomic transactions
    ├── selectors.py    # Optimized database read queries
    ├── forms.py        # Django forms & validation
    ├── views.py        # HTTP views
    ├── api/            # Serializers & viewsets
    └── tests/
```

### Full-Stack HTMX

```
myproject/
├── templates/
│   ├── layouts/base.html   # HTMX + Tailwind + Alpine.js layout
│   ├── components/         # Navbar, footer, modal
│   └── includes/           # Messages & toasts
├── apps/
│   └── dashboard/
│       ├── views/          # Full-page & partial handlers
│       ├── forms.py
│       └── templates/dashboard/
│           ├── index.html
│           └── partials/item_row.html
```

### Domain-Driven Design (DDD) & Clean Architecture

Explicit separation of concerns across Domain (entities & value objects), Application / Use Cases (interactors & DTOs), Infrastructure (Django ORM persistence adapters), and Presentation (controllers & views).

### Multi-Tenant

Shared-schema multi-tenancy with `tenancy/` providing `Tenant`, `TenantMembership`, `TenantAwareModel`, `TenantMiddleware`, and tenant-scoped querysets preventing cross-tenant data leaks.

## Environment Setup

```bash
cp .env.sample .env
```

SQLite works out of the box for development. Swap in your production database when you're ready.

## Packages

| Package | Role |
|---|---|
| Django | Web framework |
| django-environ | Environment variable management |
| django-jazzmin | Admin UI |
| djangorestframework | REST API toolkit |
| djangorestframework-simplejwt | JWT authentication |
| drf-yasg | Swagger/OpenAPI docs |
| django-cors-headers | CORS handling |
| whitenoise | Static file serving |
| gunicorn | Production WSGI server |
| psycopg[binary] | PostgreSQL driver |
| django-tailwind-cli | Tailwind CSS _(optional)_ |
| django-htmx | HTMX _(optional)_ |
| django-vite | Vite bundler _(optional)_ |

## API Endpoints

| Endpoint | Description |
|---|---|
| `/admin/` | Django admin |
| `/token/` | Obtain JWT pair |
| `/token/refresh/` | Refresh access token |
| `/docs/` | Swagger UI |
| `/schema/` | ReDoc |

## Contributing

Contributions are welcome. Open an issue or submit a PR.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/whatever`)
3. Make your changes and run `just test`
4. Submit a pull request

Match the existing code style - ruff linting and formatting are enforced.

## License

MIT © [Sankalp Tharu](https://sankalptharu.com.np)
