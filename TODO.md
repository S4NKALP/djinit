# TODO - Roadmap & Future Plans

## Completed

### Project Architectures & Scaffolding
- [x] **Add modular project architectures**:
  - [x] Modular Monolith (ERP, CRM, LMS, enterprise business domains with `common/` kernel)
  - [x] Service Layer (strict separation of models, services, selectors, views, and API)
  - [x] Full-Stack HTMX (Django Templates, HTMX partials, DaisyUI, Tailwind CSS, optional Alpine.js)
  - [x] Lightweight (minimal, zero-boilerplate preset for prototypes and MVPs)
  - [x] Domain-Driven Design (DDD with explicit domain, application, infrastructure, and presentation)
  - [x] Clean Architecture (concentric layers, use cases, interfaces, and gateway adapters)
  - [x] Multi-Tenant (shared-schema tenancy, `TenantMiddleware`, tenant-isolated models, and isolation tests)
- [x] **Architecture-Aware `djinit app`**:
  - [x] Automatic architecture detection via `.djinit.toml`
  - [x] Layered app generation matching selected architecture
  - [x] Atomic and idempotent URL include registration in `config/urls.py`
  - [x] Nested app discovery with fully-qualified `AppConfig` paths
- [x] **Project Configuration Manifest**:
  - [x] `.djinit.toml` manifest support powered by standard library `tomllib`
  - [x] Dual-write and full backward compatibility with legacy `.djinit` (JSON)
- [x] **Production Abstract Base Models**:
  - [x] `TimeStampedModel` (indexed `created_at`, `updated_at`)
  - [x] `UUIDModel` (secure non-sequential primary keys)
  - [x] `OrderedModel` (`sort_order`, `is_active`, custom ordering)
  - [x] `ActivatableModel` (boolean status toggling)
  - [x] `SoftDeleteModel` (with `SoftDeleteQuerySet`, `SoftDeleteManager`, `.delete()`, `.restore()`, `.hard_delete()`, and `.alive()`)
  - [x] `SluggedModel` (indexed unique slug fields)
  - [x] `BaseModel` (combined `UUIDModel` and `TimeStampedModel`)

### Features & Integrations
- [x] **Authentication Presets**: Opt-in Google and GitHub OAuth sign-in via `django-allauth`, with a separately selectable headless API and read-only DRF current-user serializer
- [x] **Celery, Beat & Redis**: Opt-in worker and scheduler, Redis broker and result backend, Docker Compose services, and `just worker` and `just beat` commands
- [x] **Caching Layers**: Separately selectable Redis backend for Django's default cache

### Developer Experience & Tooling
- [x] **Export to Template & Custom Starters**:
  - [x] Export existing projects with sensitive data sanitization (`.env`, `db.sqlite3`, virtual environments, cache)
  - [x] Automated parameterization of project names (`[[ project_name ]]`) and secret keys (`[[ secret_key ]]`)
  - [x] Custom template management CLI (`djinit template list`, `export`, `delete`, `apply`)
  - [x] Direct bootstrapping from custom templates via `djinit setup --template <name>`
- [x] **Interactive Configuration Wizard**:
  - [x] Categorized architecture selection (Simple, Application, Advanced)
  - [x] Architecture-dependent frontend stack prompts
  - [x] SQLite3 database URL bypass
  - [x] Rich summary confirmation
- [x] **Scripted Setup**: Generate a standard SQLite project with `djinit setup --name` and optional initial apps and integrations
- [x] **Project Doctor**: Read-only `djinit doctor [directory]` checks the manifest, project layout, environment, and Docker Compose database configuration
- [x] **Deployment Presets**:
  - [x] `Dockerfile` with multi-stage non-root container support
  - [x] `docker-compose.yml` orchestrating web service and PostgreSQL / MySQL / SQLite volumes
  - [x] Compose connects Django to the selected database and uses MySQL 8.4 for Django 6.1 compatibility
  - [x] `passenger_wsgi.py` for cPanel and Apache Phusion Passenger shared hosting
  - [x] `Procfile` and `runtime.txt` for PaaS hosting (Heroku, Render, Railway)
- [x] **CI/CD & Code Quality**:
  - [x] Modern GitHub Actions and GitLab CI workflows powered by `uv`
  - [x] Ruff linting and formatting enforcement
  - [x] Pre-commit hook configuration with latest hooks (`ruff-check`, `ruff-format`)
  - [x] Automated test suite with Pytest and live Django runtime checks (`check`, `makemigrations`, `migrate`, `test`)

---

## Upcoming Plans

### Features & Integrations
- [ ] **Django Channels / WebSockets**: Real-time event and chat capabilities
- [ ] **Cloud Storage**: AWS S3 / Cloudflare R2 / MinIO media storage presets via `django-storages`
- [ ] **Observability**: OpenTelemetry, Sentry, or Prometheus metrics integration
