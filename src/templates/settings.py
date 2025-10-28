"""
Settings management for djinit.
Handles creation and configuration of Django settings files.
"""

import os

from src.scripts.console_ui import UIFormatter
from src.scripts.secretkey_generator import generate_secret_key
from src.utils import change_cwd, create_file_with_content


class SettingsManager:
    def __init__(self, project_root: str, project_name: str, app_names: list):
        self.project_root = project_root
        self.project_name = project_name
        self.app_names = app_names
        self.project_configs = os.path.join(project_root, project_name)
        self.settings_folder = os.path.join(self.project_configs, "settings")
        self.settings_file = os.path.join(self.project_configs, "settings.py")
        self.secret_key = generate_secret_key(50)

    def create_settings_structure(self) -> bool:
        # Change to project configs directory
        with change_cwd(self.project_configs):
            # Create settings folder
            os.makedirs("settings", exist_ok=True)

            # Move settings.py to settings/base.py
            if os.path.exists(self.settings_file):
                os.rename(self.settings_file, os.path.join(self.settings_folder, "base.py"))

            # Create __init__.py files
            with change_cwd(self.settings_folder):
                open("__init__.py", "a").close()
                open("development.py", "a").close()
                open("production.py", "a").close()

        UIFormatter.print_success("Created Django settings folder structure")
        return True

    def update_base_settings(self) -> bool:
        with change_cwd(self.settings_folder):
            # Generate app list from app_names
            app_list_lines = [f'    "{app_name}",' for app_name in self.app_names]
            app_list = "\n".join(app_list_lines)

            base_content = f'''"""
Common settings shared between development and production environment
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


# Application definition
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

USER_DEFINED_APPS = [
{app_list}
]

BUILT_IN_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = BUILT_IN_APPS + THIRD_PARTY_APPS + USER_DEFINED_APPS
INSTALLED_APPS.insert(0, "jazzmin")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "{self.project_name}.urls"

TEMPLATES = [
    {{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {{
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        }},
    }},
]

WSGI_APPLICATION = "{self.project_name}.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {{
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    }},
    {{
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    }},
    {{
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    }},
    {{
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    }},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files and media files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework Settings
REST_FRAMEWORK = {{
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}}

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {{
    "TITLE": "{self.project_name} API",
    "DESCRIPTION": "API documentation for {self.project_name}",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
}}

# JWT Settings
SIMPLE_JWT = {{
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=3),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

'''

            return create_file_with_content(
                "base.py",
                base_content,
                "Updated settings/base.py with comprehensive configuration",
                should_format=True,
            )

    def update_development_settings(self) -> bool:
        """Update development.py with development-specific settings."""
        with change_cwd(self.settings_folder):
            dev_content = f"""from .base import *

SECRET_KEY = "{self.secret_key}"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }}
}}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False
"""

            return create_file_with_content(
                "development.py",
                dev_content,
                "Updated settings/development.py",
                should_format=True,
            )

    def update_production_settings(self) -> bool:
        """Update production.py with production-specific settings."""
        with change_cwd(self.settings_folder):
            prod_content = """from .base import *
import os

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

"""

            return create_file_with_content(
                "production.py",
                prod_content,
                "Updated settings/production.py",
                should_format=True,
            )
