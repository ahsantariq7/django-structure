"""
Celery configuration settings.

This module includes all Celery-related settings for asynchronous tasks,
periodic tasks, and result storage.
"""

import os
from apps.config.settings import ENVIRONMENT

# Determine environment
ENVIRONMENT = ENVIRONMENT.lower()

# CELERY CONFIGURATION
# ------------------------------------------------------------------------------
# Hardcoded Celery broker URLs based on environment
if ENVIRONMENT == "production":
    CELERY_BROKER_URL = "redis://redis:6379/0"
elif ENVIRONMENT == "staging":
    CELERY_BROKER_URL = "redis://redis:6379/0"
else:  # development
    CELERY_BROKER_URL = "redis://localhost:6379/0"

CELERY_RESULT_BACKEND = "django-db"

# Serialization
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Task specific settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Prevent memory leaks

# Task queues - define named queues for different task types
CELERY_TASK_ROUTES = {
    # Examples:
    "core.tasks.heavy_processing": {"queue": "heavy_tasks"},
    "users.tasks.*": {"queue": "user_tasks"},
    # Default queue for all other tasks
    "*": {"queue": "default"},
}

# Beat schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    # Examples:
    "cleanup-old-data": {
        "task": "core.tasks.cleanup_old_data",
        "schedule": 60 * 60 * 24,  # daily
        "options": {"expires": 60 * 60 * 2},  # 2 hours
    },
}

# Timezone for Celery Beat
CELERY_TIMEZONE = "UTC"

# Rate limiting
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Prefetch one task at a time

# Monitoring settings
CELERY_SEND_TASK_SENT_EVENT = True
