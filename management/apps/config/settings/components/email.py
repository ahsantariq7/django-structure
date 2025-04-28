"""
Email configuration settings.

This module contains all email-related settings including SMTP configuration,
email templates, and default email addresses.
"""

import os

# Email Backend Configuration
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "apps.authentication.backends.DualEmailBackend"

# SMTP Configuration
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# For development, you might want to use the console backend
if os.environ.get("DJANGO_DEBUG", "False") == "True":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Email Template Settings
# ------------------------------------------------------------------------------
EMAIL_TEMPLATE_DIR = "emails"
EMAIL_SUBJECT_PREFIX = "[Management System] "

# Email Templates Configuration
EMAIL_TEMPLATES = {
    "verification": {
        "subject": "Verify Your Email Address",
        "template": f"{EMAIL_TEMPLATE_DIR}/verification_email.html",
    },
    "welcome": {
        "subject": "Welcome to Management System",
        "template": f"{EMAIL_TEMPLATE_DIR}/welcome_email.html",
    },
    "password_reset": {
        "subject": "Reset Your Password",
        "template": f"{EMAIL_TEMPLATE_DIR}/password_reset_email.html",
    },
}
