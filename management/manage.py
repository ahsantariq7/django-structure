#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Default to development settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.development")

    # Add apps directory to Python path
    root_dir = Path(__file__).resolve().parent
    apps_dir = root_dir / "apps"
    sys.path.insert(0, str(root_dir))  # Add project root to path
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Create log directory if it doesn't exist
    log_dir = root_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
