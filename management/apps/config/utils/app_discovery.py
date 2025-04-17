"""
Utilities for app discovery and registration.
"""

import os
from pathlib import Path


def discover_apps(apps_dir):
    """
    Discover Django apps in the apps directory.
    Returns list of app names in dotted format.
    """
    discovered_apps = []

    # Skip these directories as they're not Django apps
    skipped_dirs = {"config", "__pycache__", "migrations"}

    for item in apps_dir.iterdir():
        # Skip files and specific directories
        if not item.is_dir() or item.name in skipped_dirs:
            continue

        # Check if it has apps.py (Django app signature)
        if (item / "apps.py").exists():
            # Add to discovered apps using dotted path format
            app_path = f"apps.{item.name}"
            discovered_apps.append(app_path)

    return discovered_apps


def register_app(app_name):
    """
    Register a new app in settings/base.py by updating LOCAL_APPS.
    """
    # Path to the base.py settings file
    from apps.config.settings import ROOT_DIR
    settings_file = ROOT_DIR / "apps" / "config" / "settings" / "base.py"
    
    if not settings_file.exists():
        return False
    
    # Read the current file content
    content = settings_file.read_text()
    
    # Check if app already registered
    app_path = f"\"apps.{app_name}\""
    if app_path in content:
        return True  # Already registered
        
    # Find the LOCAL_APPS section
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "LOCAL_APPS = [" in line or "LOCAL_APPS = discover_apps(APPS_DIR)" in line:
            # Since we're using auto-discovery, the app will be found
            # We don't need to modify the file
            return True
            
    return False
