# TODO - Future Plans

## Features

- [x] Docker Support: Auto generating `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- [x] Frontend Integration: Vite + React with django-vite (frontend/, vite.config.js, package.json)
- [x] Tailwind CSS: Integrated via django-tailwind-cli
- [x] HTMX: Integrated via django-htmx
- [ ] Celery: Making background tasks easier to set up
- [ ] Vue.js: Add Vue.js frontend option
- [ ] More Packages: Integrating other popular packages to help you build feature rich apps effortlessly

## Enhancements

- [x] Add more project structure templates (Standard, Predefined, Unified, Single)
- [x] Add interactive configuration wizard
- [x] Add testing framework setup (pytest, pytest-django, pytest-cov)
- [x] Improve structure detection
- [x] Fix bugs (Verified: All tests passing, no issues found)

## Project Structures

- [x] Standard Structure: `config/` module, `apps/` directory with nested apps
- [x] Predefined Structure: `apps/users`, `apps/core`, `api/` with v1
- [x] Unified Structure: `core/` as project config, `apps/` as main app
- [x] Single Folder Layout: Everything in one project folder

## Database Support

- [x] PostgreSQL
- [x] MySQL
- [x] DATABASE_URL support
