"""
Staging environment settings.

Similar to production but with more verbose logging
and potentially different service endpoints.
"""

import os
from .production import *  # noqa

# Allow more hosts in staging
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "staging.example.com,127.0.0.1").split(",")

# More verbose logging for staging
LOGGING["handlers"]["file"]["level"] = "INFO"  # noqa
LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa
LOGGING["loggers"]["core"]["level"] = "DEBUG"  # noqa
LOGGING["loggers"]["users"]["level"] = "DEBUG"  # noqa

# Optional: Different cache/db settings for staging
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.environ.get("POSTGRES_DB", "staging_db"),
#         "USER": os.environ.get("POSTGRES_USER", "staging_user"),
#         "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "staging_password"),
#         "HOST": os.environ.get("POSTGRES_HOST", "db"),
#         "PORT": os.environ.get("POSTGRES_PORT", "5432"),
#         "CONN_MAX_AGE": 60,
#     }
# }
