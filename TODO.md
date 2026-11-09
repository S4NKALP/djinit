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

### Developer Experience & Tooling
- [x] **Interactive Configuration Wizard**:
  - [x] Categorized architecture selection (Simple, Application, Advanced)
  - [x] Architecture-dependent frontend stack prompts
  - [x] SQLite3 database URL bypass
  - [x] Rich summary confirmation
- [x] **Deployment Presets**:
  - [x] `Dockerfile` with multi-stage non-root container support
  - [x] `docker-compose.yml` orchestrating web service and PostgreSQL / MySQL / SQLite volumes
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
- [ ] **Celery & Redis**: Background worker and periodic task configuration preset
- [ ] **Django Channels / WebSockets**: Real-time event and chat capabilities
- [ ] **Cloud Storage**: AWS S3 / Cloudflare R2 / MinIO media storage presets via `django-storages`
- [ ] **Authentication Presets**: Optional `django-allauth` integration for social authentication (OAuth2 / Google / GitHub)
- [ ] **Observability**: OpenTelemetry, Sentry, or Prometheus metrics integration
- [ ] **Caching Layers**: Redis cache backend configuration out of the box

### Enhancements
- [ ] **Interactive TUI**: Rich-based terminal dashboard for project health checks
- [ ] **Export to Template**: Ability to export existing projects as reusable custom templates
- [ ] **Interactive Migration Assistant**: Migration helper for updating older `djinit` projects to `.djinit.toml`
