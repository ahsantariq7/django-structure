"""
Development environment settings.

Includes debugging tools and uses PostgreSQL database.
"""

import os
from .base import *  # noqa

# Debug mode enabled for development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Debug toolbar is already included in base.py INSTALLED_APPS
# Just configure it here
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Use Django Browser Reload if not already included
if "django_browser_reload" not in INSTALLED_APPS:  # noqa
    INSTALLED_APPS += ["django_browser_reload"]  # noqa
    # Check if the middleware is already there
    if "django_browser_reload.middleware.BrowserReloadMiddleware" not in MIDDLEWARE:  # noqa
        MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa

# Use console email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# IMPORTANT: We're removing the SQLite database configuration to use PostgreSQL
# The PostgreSQL configuration comes from database.py and your environment variables

# Local memory cache for development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# Disable CSRF for development if needed
MIDDLEWARE = [m for m in MIDDLEWARE if "CsrfViewMiddleware" not in m]  # noqa

# Use normal logging in development (not the minimal version)
# This will use the configuration from components/logging.py

# Add Google OAuth credentials
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
