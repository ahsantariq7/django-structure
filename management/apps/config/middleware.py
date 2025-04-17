"""
Custom middleware for the application.
"""

import os
import logging

logger = logging.getLogger(__name__)


class EnvironmentCredentialsMiddleware:
    """
    Middleware to display environment credentials at startup.
    For development purposes only!
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.has_shown_credentials = False

    def __call__(self, request):
        if not self.has_shown_credentials:
            self._show_credentials()
            self.has_shown_credentials = True

        return self.get_response(request)

    def _show_credentials(self):
        """Print out environment credentials."""
        print("\n==================== ENVIRONMENT CREDENTIALS ====================")

        # Database settings
        print("DATABASE SETTINGS:")
        print(f"POSTGRES_DB: {os.environ.get('POSTGRES_DB', 'Not set')}")
        print(f"POSTGRES_USER: {os.environ.get('POSTGRES_USER', 'Not set')}")
        print(
            f"POSTGRES_PASSWORD: {'*' * len(os.environ.get('POSTGRES_PASSWORD', '')) if os.environ.get('POSTGRES_PASSWORD') else 'Not set'}"
        )
        print(f"POSTGRES_HOST: {os.environ.get('POSTGRES_HOST', 'Not set')}")
        print(f"POSTGRES_PORT: {os.environ.get('POSTGRES_PORT', 'Not set')}")

        # Django settings
        print("\nDJANGO SETTINGS:")
        print(f"DJANGO_ENVIRONMENT: {os.environ.get('DJANGO_ENVIRONMENT', 'Not set')}")
        print(f"DJANGO_DEBUG: {os.environ.get('DJANGO_DEBUG', 'Not set')}")
        print(
            f"DJANGO_SECRET_KEY: {'*' * len(os.environ.get('DJANGO_SECRET_KEY', '')) if os.environ.get('DJANGO_SECRET_KEY') else 'Not set'}"
        )
        print(f"DJANGO_ALLOWED_HOSTS: {os.environ.get('DJANGO_ALLOWED_HOSTS', 'Not set')}")

        # Celery settings
        print("\nCELERY SETTINGS:")
        print(f"CELERY_BROKER_URL: {os.environ.get('CELERY_BROKER_URL', 'Not set')}")

        # Redis settings
        print("\nREDIS SETTINGS:")
        print(f"REDIS_URL: {os.environ.get('REDIS_URL', 'Not set')}")

        print("==============================================================\n")

        # Also log to the logger for file logging
        logger.info("==================== ENVIRONMENT CREDENTIALS ====================")
        # Add all logger.info statements here...
