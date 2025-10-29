# djinit

<div align="center">

> PyPI did not allow the original name, so the package is released as **djinitx**

<img src="https://img.shields.io/pypi/v/djinitx?color=blue&label=PyPI&logo=pypi&logoColor=white" alt="PyPI">
<img src="https://img.shields.io/badge/Django-4.2%20%7C%205.1%20%7C%205.2-0C4B33?logo=django&logoColor=white" alt="Django">
<img src="https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python">
<a href="https://github.com/S4NKALP/djinit/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>

</div>

A fast, interactive CLI to bootstrap a modern, production‑ready Django project in minutes — featuring split settings, DRF and JWT integration, OpenAPI docs, CORS, static file handling via WhiteNoise, Postgres‑friendly configuration, CI/CD templates, deployment helpers, and battle‑tested defaults that deliver a polished developer experience out of the box.

- ✨ Split settings: `settings/base.py`, `settings/development.py`, `settings/production.py`
- 🧱 Optional nested apps layout (e.g., `apps/`)
- 🧩 App scaffolding: URLs, serializers, routes
- 🔗 Project URLs wired automatically
- 🧰 Utility files: `.gitignore`, `README.md`, `.env.sample`, `requirements.txt`, `pyproject.toml`
- 🚀 Deploy helpers: `Justfile`, `Procfile`, `runtime.txt`
- 🛠️ CI/CD: GitHub Actions and/or GitLab CI
- 🎨 Polished UX with `rich`

---

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

Requirements: Python 3.13+

## Quick start

Run the interactive setup:

```bash
djinit setup
# or
dj setup
```

Prompts include:

- Project directory
- Django project name (used by `django-admin startproject`)
- Apps layout (flat vs nested package like `apps/`)
- App names (comma‑separated)
- CI/CD choice (GitHub, GitLab, both, none)
- Database config preference (`DATABASE_URL` vs individual params)

## Commands

- `djinit setup` or `dj setup` — Launch the interactive project generator
- `djinit app <names>` or `dj app <names>` — Create one or more Django apps in an existing project
  - Examples:
    - `djinit app users` or `dj app users`
    - `djinit app users,products,orders` or `dj app users,products,orders`
    - `djinit app users products orders` or `dj app users products orders`
- `djinit secret [--count N] [--length L]` or `dj secret [--count N] [--length L]` — Print random Django `SECRET_KEY` values
  - Example: `djinit secret --count 5 --length 50`

## What gets generated

- Django project and apps, then structure validation
- Settings package and split settings
- Base/development/production settings
- Utility files
- App files: `urls.py`, `serializers.py`, `routes.py`
- Project `urls.py` (auto‑includes your apps)
- Updated `wsgi.py`, `asgi.py`, `manage.py`
- `Justfile`, `Procfile`, `runtime.txt`
- CI/CD workflows (per your selection)

### Output highlights

- `config/settings/` → `__init__.py`, `base.py`, `development.py`, `production.py`
- `apps/<app>/` → `urls.py`, `serializers.py`, `routes.py`
- Project root → `.gitignore`, `README.md`, `.env.sample`, `requirements.txt`, `pyproject.toml`, `Justfile`, `Procfile`, `runtime.txt`
- CI/CD → `.github/workflows/` and/or `.gitlab-ci.yml`

Note: If you choose a nested apps package (e.g., `apps`), imports and `INSTALLED_APPS` entries are configured accordingly.

## Included packages (by default)

Generated `requirements.txt` includes:

- Django
- python-dotenv
- django-jazzmin
- djangorestframework
- djangorestframework-simplejwt
- drf-spectacular
- django-cors-headers
- whitenoise
- psycopg2-binary
- gunicorn
- dj-database-url (when you opt into `DATABASE_URL`)

These give you a ready‑to‑use stack with DRF, JWT auth, OpenAPI schema generation, CORS, static files in production, and Postgres support.

## Environment and database

- A `.env.sample` is generated to get you started.
- If you opt into `DATABASE_URL`, `production.py` expects an environment variable like:
  `postgres://user:password@host:port/database`

## Contributing

Contributions are welcome!
Please open an issue for bugs/ideas. PRs with clear descriptions are appreciated.

## Acknowledgments

- Django and the Django community
- Jinja2
- rich
- click
- ruff

## License

MIT © Sankalp Tharu
