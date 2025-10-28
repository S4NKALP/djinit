"""
CI/CD pipeline manager for djinit
Handles creation of Github Actions and GitLab CI onfigurations
"""

import os
from src.utils import change_cwd, create_file_with_content


class CiCDConfigGenerator:
    def __init__(self, project_root: str, project_name: str):
        self.project_root = project_root
        self.project_name = project_name

    def create_github_actions(self) -> bool:
        with change_cwd(self.project_root):
            github_dir = os.path.join(self.project_root, ".github", "workflows")
            os.makedirs(github_dir, exist_ok=True)

        workflow_content = f"""name: Django CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v5
      with:
        python-version: ${{{{ matrix.python-version }}}}

    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"

    - name: Install dependencies
      run: uv sync

    - name: Run linting
      run: uv run ruff check .

    - name: Format check
      run: uv run ruff format --check .

    - name: Set up PostgreSQL
      env:
        DB_NAME: test_db
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_HOST: localhost
        DB_PORT: 5432
      run: |
        echo "PostgreSQL is ready"

    - name: Run Django tests
      env:
        DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
        SECRET_KEY: test-secret-key-for-ci
        ALLOWED_HOSTS: localhost
        DB_NAME: test_db
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_HOST: localhost
        DB_PORT: 5432
      run: |
        uv run python manage.py check
        uv run python manage.py test

    - name: Check migrations
      env:
        DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
        SECRET_KEY: test-secret-key-for-ci
        ALLOWED_HOSTS: localhost
        DB_NAME: test_db
        DB_USER: postgres
        DB_PASSWORD: postgres
        DB_HOST: localhost
        DB_PORT: 5432
      run: |
        uv run python manage.py makemigrations --check --dry-run

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.13"

    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"

    - name: Install dependencies
      run: uv sync

    - name: Run security check
      run: uv run python manage.py check --deploy
"""

        workflow_file = os.path.join(github_dir, "ci.yml")
        create_file_with_content(
            workflow_file,
            workflow_content,
            f"Created Github Actions workflow ({workflow_file})",
        )
        return True

    def create_gitlab_ci(self) -> bool:
        with change_cwd(self.project_root):
            gitlab_ci_content = f"""# GitLab CI/CD configuration for {self.project_name}

stages:
  - test
  - lint
  - security

variables:
  POSTGRES_DB: test_db
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres
  DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/test_db"

# Use Docker-in-Docker
services:
  - postgres:15

before_script:
  - python --version
  - pip install uv
  - uv sync

# Lint stage
lint:
  stage: lint
  image: python:3.13
  script:
    - uv run ruff check .
    - uv run ruff format --check .
  only:
    - branches
    - merge_requests

# Test stage
test:
  stage: test
  image: python:3.13
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
    ALLOWED_HOSTS: localhost
  script:
    - uv run python manage.py check
    - uv run python manage.py migrate
    - uv run python manage.py test
  only:
    - branches
    - merge_requests

# Multiple Python versions
test:python310:
  stage: test
  image: python:3.10
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
    ALLOWED_HOSTS: localhost
  script:
    - pip install uv
    - uv sync
    - uv run python manage.py check
    - uv run python manage.py migrate
    - uv run python manage.py test
  only:
    - branches
    - merge_requests

test:python311:
  stage: test
  image: python:3.11
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
    ALLOWED_HOSTS: localhost
  script:
    - pip install uv
    - uv sync
    - uv run python manage.py check
    - uv run python manage.py migrate
    - uv run python manage.py test
  only:
    - branches
    - merge_requests

test:python312:
  stage: test
  image: python:3.12
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
    ALLOWED_HOSTS: localhost
  script:
    - pip install uv
    - uv sync
    - uv run python manage.py check
    - uv run python manage.py migrate
    - uv run python manage.py test
  only:
    - branches
    - merge_requests

test:python313:
  stage: test
  image: python:3.13
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
    ALLOWED_HOSTS: localhost
  script:
    - pip install uv
    - uv sync
    - uv run python manage.py check
    - uv run python manage.py migrate
    - uv run python manage.py test
  only:
    - branches
    - merge_requests

# Security check
security:
  stage: security
  image: python:3.13
  variables:
    DJANGO_SETTINGS_MODULE: {self.project_name}.settings.development
    SECRET_KEY: test-secret-key-for-ci
  script:
    - pip install uv
    - uv sync
    - uv run python manage.py check --deploy
    - uv run python manage.py validate_templates
  only:
    - main
    - develop
"""
            config_file = ".gitlab_ci_content"
            create_file_with_content(
                config_file,
                gitlab_ci_content,
                f"Created GitLab CI configuration ({config_file})",
            )
            return True
