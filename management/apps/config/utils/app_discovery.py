"""
Utility functions for discovering Django apps in the project.
"""

import os
from pathlib import Path


def is_django_app(directory):
    """Check if a directory is a Django app by looking for apps.py"""
    return (Path(directory) / "apps.py").exists()


def discover_apps(base_dir, include_subdirs=True):
    """
    Discover Django apps in the given directory and its subdirectories.
    Returns a list of dotted module paths for discovered apps.
    """
    apps = []
    base_dir = Path(base_dir)

    # Get the project root directory
    project_root = base_dir.parent if base_dir.name == "apps" else base_dir.parent.parent

    # Function to get module path relative to project root
    def get_module_path(app_dir):
        rel_path = app_dir.relative_to(project_root)
        return str(rel_path).replace(os.sep, ".")

    # First check directly in the base directory
    for item in base_dir.iterdir():
        if item.is_dir() and is_django_app(item):
            apps.append(get_module_path(item))

    # Now look in subdirectories if requested
    if include_subdirs:
        # Use os.walk to find all subdirectories
        for root, dirs, _ in os.walk(str(base_dir)):
            root_path = Path(root)
            # Skip the root directory as we already checked it
            if root_path == base_dir:
                continue

            for dir_name in dirs:
                dir_path = root_path / dir_name
                if is_django_app(dir_path):
                    module_path = get_module_path(dir_path)
                    if module_path not in apps:
                        apps.append(module_path)

    return apps


def discover_all_apps(root_dir):
    """
    Discover all Django apps in the project, including custom directories.
    """
    root_dir = Path(root_dir)
    apps_dir = root_dir / "apps"
    all_apps = []

    # Discover apps in the standard apps directory (including nested apps)
    all_apps.extend(discover_apps(apps_dir, include_subdirs=True))

    # Discover apps in other directories at the project root level
    for item in root_dir.iterdir():
        if item.is_dir() and item.name != "apps" and not item.name.startswith("."):
            # Skip common non-app directories
            if item.name in {"venv", ".venv", "env", "media", "static", "__pycache__"}:
                continue

            # Check for Django apps in this directory and its subdirectories
            if is_django_app(item):
                module_path = item.name
                all_apps.append(module_path)

            # Also check subdirectories
            all_apps.extend(discover_apps(item, include_subdirs=True))

    return all_apps


def register_app(app_name):
    """
    Register a new app in settings/base.py by updating INSTALLED_APPS.
    """
    from django.conf import settings

    # Path to the settings file
    settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"

    if not settings_file.exists():
        return False

    content = settings_file.read_text()

    # Check if the app is already registered
    if f"'{app_name}'" in content or f'"{app_name}"' in content:
        return True

    # Find a good place to add the app
    # First try LOCAL_APPS
    if "LOCAL_APPS = [" in content:
        new_content = content.replace("LOCAL_APPS = [", f"LOCAL_APPS = [\n    '{app_name}',")
    # If not, try INSTALLED_APPS directly
    elif "INSTALLED_APPS = [" in content:
        new_content = content.replace(
            "INSTALLED_APPS = [", f"INSTALLED_APPS = [\n    '{app_name}',"
        )
    else:
        return False

    # Write the updated content
    settings_file.write_text(new_content)
    return True
