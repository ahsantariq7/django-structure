"""
Base settings for the Django application.

This module contains the foundation settings that are common to all environments.
Settings are imported from component modules for better organization.
"""

import os
from pathlib import Path

# Import constants from settings.__init__
from apps.config.settings import ROOT_DIR, APPS_DIR, LOGS_DIR

# Import component settings - order matters here
from apps.config.settings.components.logging import *  # noqa
from apps.config.settings.components.security import *  # noqa
from apps.config.settings.components.database import *  # noqa
from apps.config.settings.components.caching import *  # noqa
from apps.config.settings.components.celery import *  # noqa
from apps.config.settings.components.rest import *  # noqa
from apps.config.settings.components.email import *  # noqa

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation
TIME_ZONE = "UTC"
# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"
# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "authentication.User"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "apps.authentication.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# STATIC FILES CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR / "static")
# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_DIRS = [
    # str(ROOT_DIR / "static_assets"),  # For project-wide static files
]

# MEDIA FILES CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(ROOT_DIR / "media")

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(ROOT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Custom context processors can be added here
            ],
        },
    },
]

# APPLICATION CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_spectacular",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "debug_toolbar",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_celery_results",
    "django_celery_beat",
    "corsheaders",
    "django_browser_reload",
]

# Settings for application discovery and loading
# ===========================================================

# Auto-discover all apps in the project
try:
    from apps.config.utils.app_discovery import discover_apps, discover_all_apps

    # Get apps from the standard apps directory (including nested ones)
    LOCAL_APPS = discover_apps(APPS_DIR, include_subdirs=True)

    # Discover apps in custom directories
    CUSTOM_APPS = []

    try:
        # Get all apps throughout the project
        all_apps = discover_all_apps(ROOT_DIR)

        # Filter out the ones already in the standard apps directory
        CUSTOM_APPS = [app for app in all_apps if app not in LOCAL_APPS]
    except Exception as e:
        print(f"Warning: Error discovering custom apps: {e}")

except ImportError:
    # Fallback if app_discovery module is not available
    LOCAL_APPS = []
    CUSTOM_APPS = []

# Combine all the app lists
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + CUSTOM_APPS + ["apps.config"]

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    # Security middleware
    "django.middleware.security.SecurityMiddleware",
    # Environment credentials middleware - place it higher in the list
    "apps.config.middleware.EnvironmentCredentialsMiddleware",
    # CORS middleware - must be before CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    # Django standard middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Add Debug Toolbar middleware
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

# URL CONFIGURATION
# ------------------------------------------------------------------------------
ROOT_URLCONF = "apps.config.urls.base"

# WSGI/ASGI CONFIGURATION
# ------------------------------------------------------------------------------
WSGI_APPLICATION = "apps.config.wsgi.application"
ASGI_APPLICATION = "apps.config.asgi.application"

# Swagger Settings
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {"Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}},
    "USE_SESSION_AUTH": False,
    "JSON_EDITOR": True,
}

# ReDoc Settings
REDOC_SETTINGS = {
    "LAZY_RENDERING": True,
    "NATIVE_SCROLLBARS": True,
    "REQUIRED_PROPS_FIRST": True,
    "NO_AUTO_AUTH": True,
}

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Management API",
    "DESCRIPTION": "API documentation for Management System",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
    },
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_SPLIT_RESPONSE": True,
    "SORT_OPERATIONS": True,
    "TAGS_SORTER": "alpha",
    "OPERATIONS_SORTER": "alpha",
    "DOC_EXPANSION": "none",
    "DEFAULT_MODEL_RENDERING": "example",
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.authentication.backends.CustomJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
