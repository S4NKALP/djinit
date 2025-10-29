# core

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
core/
├── core/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── store/
├── manage.py
├── requirements.txt
├── pyproject.toml
├── .env.sample
└── README.md
```

## API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs/
- Schema: http://localhost:8000/schema/
