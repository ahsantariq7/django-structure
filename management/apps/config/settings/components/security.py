"""
Security configuration settings.

This module contains all security-related settings including password validation,
secret key, CSRF protection, and secure headers.
"""

import os
from datetime import timedelta

# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# Secret key - required for secure sessions, CSRF, etc.
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-development-key")

# Debug mode - NEVER enable in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# Hosts/domain names that are allowed to serve this site
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SAMESITE = "Lax"

# Session security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_COOKIE_SAMESITE = "Lax"

# Clickjacking protection
X_FRAME_OPTIONS = "DENY"

# Content Security Policy
# See: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
)  # Allow inline styles for admin
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
)  # Allow inline scripts for admin
CSP_IMG_SRC = (
    "'self'",
    "data:",
)  # Allow data URLs for images
CSP_FONT_SRC = ("'self'",)

# Secure headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HTTP Strict Transport Security (only in production)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Secure SSL Redirect (only in production)
SECURE_SSL_REDIRECT = not DEBUG
