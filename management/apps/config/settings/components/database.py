"""
Database configuration settings.

This module includes all database-related settings including connection,
pooling, and migration configurations.
"""

import os
from apps.config.settings import ROOT_DIR, ENVIRONMENT

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Hardcoded database configurations for different environments
ENVIRONMENT = ENVIRONMENT.lower()

if ENVIRONMENT == "production":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "proddatabase",
            "USER": "produser",
            "PASSWORD": "prodpassword",
            "HOST": "db",
            "PORT": "5432",
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "connect_timeout": 10,
                "application_name": "django_app_prod",
            },
        }
    }
elif ENVIRONMENT == "staging":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "stagingdb",
            "USER": "staginguser",
            "PASSWORD": "stagingpassword",
            "HOST": "db",
            "PORT": "5432",
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "connect_timeout": 10,
                "application_name": "django_app_staging",
            },
        }
    }
else:  # development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "devdatabase",
            "USER": "devuser",
            "PASSWORD": "devpassword",
            "HOST": "localhost",
            "PORT": "5432",
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "connect_timeout": 10,
                "application_name": "django_app_dev",
            },
        }
    }

# For dj-database-url compatibility (if needed)
try:
    import dj_database_url
    
    # Set database URL based on environment
    if ENVIRONMENT == "production":
        DATABASE_URL = "postgres://produser:prodpassword@db:5432/proddatabase"
    elif ENVIRONMENT == "staging":
        DATABASE_URL = "postgres://staginguser:stagingpassword@db:5432/stagingdb"
    else:  # development
        DATABASE_URL = "postgres://devuser:devpassword@localhost:5432/devdatabase"
    
    DATABASES["default"].update(
        dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=DATABASES["default"]["CONN_MAX_AGE"],
        )
    )
except ImportError:
    pass
