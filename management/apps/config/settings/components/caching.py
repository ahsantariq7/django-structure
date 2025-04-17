"""
Caching configuration settings.

This module includes all cache-related settings including Redis and
in-memory caching options.
"""

import os
from apps.config.settings import ENVIRONMENT

# CACHE CONFIGURATION
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/1"),
        "KEY_PREFIX": "myapp",  # Prefix all cache keys
        "OPTIONS": {
            "client_class": "django_redis.client.DefaultClient",
            "socket_connect_timeout": 5,  # seconds
            "socket_timeout": 5,  # seconds
            "ignore_exceptions": True,  # Don't crash on Redis errors
        },
    }
}

# Session cache configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# Consider where to use caching
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = "myapp"


# Smart cache key function for template fragments
def make_template_fragment_key(fragment_name, vary_on=None):
    if vary_on is None:
        vary_on = ()
    key = ":".join(str(var) for var in vary_on)
    return f"template.cache.{fragment_name}.{key}"
