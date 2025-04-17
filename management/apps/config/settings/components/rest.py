"""
REST Framework configuration settings.

This module contains all settings related to Django REST Framework
including authentication, permissions, and throttling.
"""

import os
from datetime import timedelta

# REST FRAMEWORK CONFIGURATION
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Default authentication classes
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Default permission classes
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Default pagination class
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.environ.get("API_PAGE_SIZE", 10)),
    # Throttling settings
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("API_THROTTLE_ANON", "100/day"),
        "user": os.environ.get("API_THROTTLE_USER", "1000/day"),
    },
    # Versioning
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    "DEFAULT_VERSION": "1.0",
    "ALLOWED_VERSIONS": ["1.0"],
    # Renderer settings
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        # Only include browsable API in development
    ],
    # Parser settings
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    # Exception handling
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    # Content negotiation
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "rest_framework.negotiation.DefaultContentNegotiation",
    # Schema
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# DRF SPECTACULAR SETTINGS
# ------------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Management API",
    "DESCRIPTION": "API documentation for Management system",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Optional UI customization
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    # Patterns to exclude from schema
    "SCHEMA_PATH_PREFIX": r"/api/",
    # Add custom configurations
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        # {"name": "auth", "description": "Authentication operations"},
        # {"name": "users", "description": "User management"},
        # {"name": "api", "description": "API operations"},
        # Add more tags as you add more apps
    ],
}

# CORS settings - control which domains can access the API
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",  # Support request ID tracking
]

# SIMPLE JWT CONFIGURATION
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ.get("SECRET_KEY"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=60),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=7),
}
