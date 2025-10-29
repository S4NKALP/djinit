from .base import *

SECRET_KEY = "+#JJBTL^S&N7FOYi8_WM$*(BvxD6VqB7JnLCvgO_4f9yN$FJP8"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False
