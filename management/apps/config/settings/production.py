"""
Production environment settings.

Security-focused settings for live deployment with
performance optimizations.
"""

import os
from .base import *  # noqa

# Force DEBUG to be False in production
DEBUG = False

# Allowed hosts must come from environment variables in production
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS:
    raise Exception("DJANGO_ALLOWED_HOSTS environment variable not set!")

# Security settings - already defined in components/security.py
# but explicitly ensure they're enabled in production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static and media file storage
# Uncomment if using S3 for production storage
# AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
# AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
# AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# AWS_DEFAULT_ACL = "public-read"
# AWS_LOCATION = "static"
# STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

# Logging - adjust levels for production
LOGGING["handlers"]["file"]["level"] = "ERROR"  # noqa
LOGGING["loggers"]["django"]["level"] = "ERROR"  # noqa

# Ensure sensitive values are set
REQUIRED_ENV_VARS = ["DJANGO_SECRET_KEY", "POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_DB"]

for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var):
        raise Exception(f"Required environment variable {var} is not set!")
