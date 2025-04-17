"""
ASGI config for the project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from django.core.asgi import get_asgi_application

# Default to production settings for ASGI
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.production")

application = get_asgi_application()
