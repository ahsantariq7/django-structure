"""
Celery configuration for asynchronous tasks.

This module configures the Celery instance that runs background tasks,
periodic tasks, and other asynchronous operations.
"""

import os
import logging
from celery import Celery
from celery.signals import task_failure, worker_ready

# Configure logging
logger = logging.getLogger(__name__)

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.development")

# Create Celery application
app = Celery("management")

# Use Django settings for Celery configuration
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load tasks from all registered Django apps
app.autodiscover_tasks()


# Celery signals for monitoring and logging
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Log details when a task fails."""
    logger.error(
        f"Task {sender.name} with ID {task_id} failed: {exception}",
        exc_info=exception,
        extra={"task_id": task_id},
    )


@worker_ready.connect
def log_worker_ready(**kwargs):
    """Log when a worker comes online."""
    logger.info("Celery worker is ready")


@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "success", "message": "Debug task executed successfully"}


# Configure task routing
app.conf.task_routes = {
    "core.tasks.*": {"queue": "core"},
    "users.tasks.*": {"queue": "users"},
}

# Task soft time limit
app.conf.task_soft_time_limit = 60 * 5  # 5 minutes


@app.task(bind=True, name="test_celery")
def test_celery(self):
    """Test task to verify Celery is working."""
    print("Celery is working!")
    logger.info("Celery test task executed successfully")
    return {"status": "success", "message": "Celery is working correctly"}


# To run this test task:
from celery_app import test_celery

test_celery.delay()


@app.task(name="celery.status")
def celery_status():
    """Return a message confirming that Celery is working."""
    message = "Celery is working correctly!"
    logger.info(message)
    return {
        "status": "success",
        "message": message,
        "environment": os.environ.get("DJANGO_ENVIRONMENT", "development"),
    }


@worker_ready.connect
def at_worker_ready(sender, **kwargs):
    """Log when the worker is ready."""
    logger.info(f"Celery worker '{sender.hostname}' is ready.")
    logger.info(f"Using broker: {app.conf.broker_url}")
