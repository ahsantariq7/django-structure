"""
Custom management command to move a Django app from one location to another.
"""

import os
import sys
import shutil
import importlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import re


class Command(BaseCommand):
    help = "Moves a Django app from one location to another and updates all references"

    def add_arguments(self, parser):
        parser.add_argument("app_name", help="Name of the app to move")
        parser.add_argument(
            "source_dir",
            help="Source directory where the app is currently located (relative to project root)",
        )
        parser.add_argument(
            "target_dir",
            help="Target directory where the app should be moved to (relative to project root)",
        )
        parser.add_argument("--force", action="store_true", help="Force move without confirmation")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be done without making changes"
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        source_dir = options["source_dir"]
        target_dir = options["target_dir"]
        force = options.get("force", False)
        dry_run = options.get("dry_run", False)

        # Normalize paths
        source_dir = source_dir.rstrip("/")
        target_dir = target_dir.rstrip("/")

        # Determine the app's source and target locations
        source_app_dir = Path(settings.ROOT_DIR) / source_dir / app_name
        target_app_dir = Path(settings.ROOT_DIR) / target_dir / app_name

        # Check if source app exists
        if not source_app_dir.exists() or not (source_app_dir / "apps.py").exists():
            raise CommandError(f"App '{app_name}' not found in directory '{source_dir}'")

        # Check if target directory exists
        if not (Path(settings.ROOT_DIR) / target_dir).exists():
            raise CommandError(f"Target directory '{target_dir}' does not exist")

        # Check if target app already exists
        if target_app_dir.exists():
            if not force:
                raise CommandError(
                    f"App '{app_name}' already exists in directory '{target_dir}'. "
                    "Use --force to overwrite."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"App '{app_name}' already exists in '{target_dir}'. It will be overwritten."
                )
            )

        # Confirm before proceeding
        if not force and not dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"This will move app '{app_name}' from '{source_dir}' to '{target_dir}'."
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "This operation will update all references to the app throughout the project."
                )
            )
            if input("Are you sure you want to continue? [y/N] ") != "y":
                self.stdout.write(self.style.ERROR("Operation cancelled."))
                return

        # Calculate module paths
        old_module_path = f"{source_dir.replace('/', '.')}.{app_name}"
        new_module_path = f"{target_dir.replace('/', '.')}.{app_name}"

        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY RUN - No changes will be made"))
            self.stdout.write(f"Would move app '{app_name}' from '{source_dir}' to '{target_dir}'")
            self.stdout.write(f"Old module path: {old_module_path}")
            self.stdout.write(f"New module path: {new_module_path}")
            self._show_changes(old_module_path, new_module_path, app_name)
            return

        # Move the app directory
        self.stdout.write(f"Moving app '{app_name}' from '{source_dir}' to '{target_dir}'...")

        # Create target directory if it doesn't exist
        os.makedirs(target_app_dir.parent, exist_ok=True)

        # Copy the app directory
        shutil.copytree(source_app_dir, target_app_dir, dirs_exist_ok=True)

        # Update app references
        self._update_settings(old_module_path, new_module_path)
        self._update_urls(old_module_path, new_module_path, app_name)
        self._update_imports(old_module_path, new_module_path, app_name)

        # Remove the old app directory
        shutil.rmtree(source_app_dir)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully moved app '{app_name}' from '{source_dir}' to '{target_dir}'"
            )
        )
        self.stdout.write(
            self.style.SUCCESS("All references have been updated throughout the project")
        )

    def _show_changes(self, old_module_path, new_module_path, app_name):
        """Show what changes would be made without actually making them."""
        self.stdout.write("\nWould update the following files:")

        # Check settings
        settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"
        if settings_file.exists():
            content = settings_file.read_text()
            if old_module_path in content:
                self.stdout.write(f"- {settings_file}")

        # Check URLs
        urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"
        if urls_file.exists():
            content = urls_file.read_text()
            if old_module_path in content or f"apps.{app_name}" in content:
                self.stdout.write(f"- {urls_file}")

        # Check for imports in Python files
        for root, _, files in os.walk(settings.ROOT_DIR):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text()
                        if old_module_path in content or f"apps.{app_name}" in content:
                            self.stdout.write(f"- {file_path}")
                    except Exception:
                        pass

    def _update_settings(self, old_module_path, new_module_path):
        """Update app references in settings files."""
        settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"
        if settings_file.exists():
            content = settings_file.read_text()
            if old_module_path in content:
                new_content = content.replace(old_module_path, new_module_path)
                settings_file.write_text(new_content)
                self.stdout.write(f"Updated references in {settings_file}")

    def _update_urls(self, old_module_path, new_module_path, app_name):
        """Update app references in URL configuration files."""
        urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"
        if urls_file.exists():
            content = urls_file.read_text()

            # Look for URL patterns with either single or double quotes
            old_pattern_double = f'path("{app_name}/"'
            old_pattern_single = f"path('{app_name}/'"
            old_namespace_double = f'namespace="{app_name}"'
            old_namespace_single = f"namespace='{app_name}'"
            old_include_double = f'include("{old_module_path}'
            old_include_single = f"include('{old_module_path}"

            # New patterns for replacement
            new_pattern_double = f'path("{app_name}/"'
            new_pattern_single = f"path('{app_name}/'"
            new_namespace_double = f'namespace="{app_name}"'
            new_namespace_single = f"namespace='{app_name}'"
            new_include_double = f'include("{new_module_path}'
            new_include_single = f"include('{new_module_path}"

            # Prepare replacement mapping
            replacements = [
                (old_include_double, new_include_double),
                (old_include_single, new_include_single),
            ]

            # Apply replacements
            new_content = content
            for old, new in replacements:
                new_content = new_content.replace(old, new)

            if new_content != content:
                urls_file.write_text(new_content)
                self.stdout.write(f"Updated URL patterns in {urls_file}")

    def _update_imports(self, old_module_path, new_module_path, app_name):
        """Update import statements in Python files."""
        # Common import patterns to update
        import_patterns = [
            f"from {old_module_path}",
            f"import {old_module_path}",
            f"from apps.{app_name}",
            f"import apps.{app_name}",
        ]

        # Walk through all Python files in the project
        for root, _, files in os.walk(settings.ROOT_DIR):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text()
                        new_content = content

                        # Apply replacements
                        for pattern in import_patterns:
                            if pattern in content:
                                new_pattern = pattern.replace(
                                    old_module_path, new_module_path
                                ).replace(f"apps.{app_name}", f"{new_module_path}")
                                new_content = new_content.replace(pattern, new_pattern)

                        if new_content != content:
                            file_path.write_text(new_content)
                            self.stdout.write(f"Updated imports in {file_path}")
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"Could not update imports in {file_path}: {e}")
                        )


def move_app_standalone(
    app_name, source_dir, target_dir, force=False, dry_run=False, project_root=None
):
    """
    Standalone function to move a Django app from one location to another.
    This can be used in scripts without the full Django management command infrastructure.
    """
    if project_root is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Set up Django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    # Import Django settings
    import django

    django.setup()

    # Create and run the command
    from django.core.management import call_command

    call_command("moveapp", app_name, source_dir, target_dir, force=force, dry_run=dry_run)
