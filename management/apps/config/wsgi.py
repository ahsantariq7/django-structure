"""
WSGI config for the project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

# Default to production settings for WSGI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.production")

application = get_wsgi_application()
