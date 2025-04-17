"""
Django settings initialization.

This module provides a smart settings loader that detects which
settings to use based on environment variables.
"""

import os
import sys
from pathlib import Path

# Make the root path available
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Add the root directory to the Python path
sys.path.append(str(ROOT_DIR))

# Create logs directory
LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Smart environment detection with explicit fallback
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "development").lower()

# Set the default Django settings module
if ENVIRONMENT == "production":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.production")
elif ENVIRONMENT == "staging":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.staging")
elif ENVIRONMENT == "testing":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.testing")
else:  # Default to development
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.development")

# Export useful path constants
APPS_DIR = ROOT_DIR / "apps"
