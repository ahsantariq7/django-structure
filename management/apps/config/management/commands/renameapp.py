"""
Custom management command to rename a Django app with all necessary changes.
"""

import os
import sys
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = "Renames a Django app throughout the project"

    def add_arguments(self, parser):
        parser.add_argument("old_name", help="Current name of the app")
        parser.add_argument("new_name", help="New name for the app")
        parser.add_argument(
            "--force", action="store_true", help="Force rename without confirmation"
        )

    def _update_urls(self, old_name, new_name):
        """Update app URLs in the main URL configuration"""
        try:
            # Locate the main URL configuration file
            base_urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"

            if base_urls_file.exists():
                content = base_urls_file.read_text()

                # Look for URL patterns with either single or double quotes
                old_pattern_double = f'path("{old_name}/"'
                old_pattern_single = f"path('{old_name}/'"
                old_namespace_double = f'namespace="{old_name}"'
                old_namespace_single = f"namespace='{old_name}'"

                # New patterns for replacement
                new_pattern_double = f'path("{new_name}/"'
                new_pattern_single = f"path('{new_name}/'"
                new_namespace_double = f'namespace="{new_name}"'
                new_namespace_single = f"namespace='{new_name}'"

                # Prepare replacement mapping
                replacements = [
                    (f'path("{old_name}/', f'path("{new_name}/'),
                    (f"path('{old_name}/'", f"path('{new_name}/'"),
                    (f'include("apps.{old_name}', f'include("apps.{new_name}'),
                    (f"include('apps.{old_name}", f"include('apps.{new_name}"),
                    (f'namespace="{old_name}"', f'namespace="{new_name}"'),
                    (f"namespace='{old_name}'", f"namespace='{new_name}'"),
                ]

                # Apply all replacements
                for old, new in replacements:
                    content = content.replace(old, new)

                # Write updated content
                base_urls_file.write_text(content)
                self.stdout.write(
                    self.style.SUCCESS(f"Updated URL configuration in {base_urls_file}")
                )
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(f"URL configuration file not found at {base_urls_file}")
                )
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating URL configuration: {e}"))
            return False

    def _update_settings(self, old_name, new_name):
        """Update app name in settings.py"""
        try:
            settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"

            if settings_file.exists():
                content = settings_file.read_text()
                old_app_path = f'"apps.{old_name}"'
                new_app_path = f'"apps.{new_name}"'

                # Replace the app name in INSTALLED_APPS
                if old_app_path in content:
                    content = content.replace(old_app_path, new_app_path)
                    settings_file.write_text(content)
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated app name in settings file: {settings_file}")
                    )
                    return True
                else:
                    self.stdout.write(
                        self.style.NOTICE(f"App '{old_name}' not explicitly listed in settings")
                    )
            else:
                self.stdout.write(self.style.WARNING(f"Settings file not found at {settings_file}"))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating settings: {e}"))
            return False

    def _update_migrations(self, old_name, new_name):
        """Update app name in migration records"""
        try:
            with connection.cursor() as cursor:
                # Update app name in django_migrations table
                cursor.execute(
                    "UPDATE django_migrations SET app = %s WHERE app = %s", [new_name, old_name]
                )
                count = cursor.rowcount
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {count} migration records in database")
                )
                return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating migrations in database: {e}"))
            return False

    def _update_app_references(self, old_name, new_name, app_dir):
        """Update references within the app files"""
        try:
            # Walk through all Python files in the app
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    if file.endswith(".py"):
                        file_path = Path(root) / file
                        content = file_path.read_text()

                        # Replace imports and references
                        updated_content = (
                            content.replace(f"apps.{old_name}", f"apps.{new_name}")
                            .replace(f"from {old_name} import", f"from {new_name} import")
                            .replace(f"from {old_name}.", f"from {new_name}.")
                            .replace(f"app_name = '{old_name}'", f"app_name = '{new_name}'")
                            .replace(f'app_name = "{old_name}"', f'app_name = "{new_name}"')
                        )

                        if content != updated_content:
                            file_path.write_text(updated_content)
                            self.stdout.write(
                                self.style.SUCCESS(f"Updated references in {file_path}")
                            )
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating app references: {e}"))
            return False

    def handle(self, *args, **options):
        old_name = options["old_name"]
        new_name = options["new_name"]
        force = options["force"]

        # Validate names
        if not old_name.isalnum() or not new_name.isalnum():
            raise CommandError("App names should be alphanumeric")

        # Get paths
        old_app_dir = settings.APPS_DIR / old_name
        new_app_dir = settings.APPS_DIR / new_name

        # Check if old app exists
        if not old_app_dir.exists():
            raise CommandError(f"App '{old_name}' does not exist at {old_app_dir}")

        # Check if it's a Django app
        if not (old_app_dir / "apps.py").exists():
            raise CommandError(
                f"The directory '{old_app_dir}' does not appear to be a Django app (no apps.py found)"
            )

        # Check if new app name already exists
        if new_app_dir.exists():
            raise CommandError(f"App '{new_name}' already exists at {new_app_dir}")

        # Ask for confirmation
        if not force:
            self.stdout.write(
                self.style.WARNING(f"You are about to rename app '{old_name}' to '{new_name}'")
            )
            confirm = input("Are you sure you want to proceed? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.SUCCESS("App renaming cancelled."))
                return

        # Update references first (before renaming directory)
        self._update_app_references(old_name, new_name, old_app_dir)

        # Update URLs
        self._update_urls(old_name, new_name)

        # Update settings
        self._update_settings(old_name, new_name)

        # Update migrations
        self._update_migrations(old_name, new_name)

        # Copy old app to new location with new name
        try:
            shutil.copytree(old_app_dir, new_app_dir)
            self.stdout.write(self.style.SUCCESS(f"Created new app at {new_app_dir}"))
        except Exception as e:
            raise CommandError(f"Error creating new app directory: {e}")

        # Remove old app directory
        try:
            shutil.rmtree(old_app_dir)
            self.stdout.write(self.style.SUCCESS(f"Removed old app directory at {old_app_dir}"))
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Error removing old app directory: {e}. You may need to remove it manually."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully renamed app from '{old_name}' to '{new_name}'")
        )
        self.stdout.write(
            self.style.WARNING(
                "Note: You may need to restart your Django server for all changes to take effect"
            )
        )

def rename_app_standalone(old_name, new_name, force=False, project_root=None):
    """Standalone function to rename an app without requiring Django to start"""
    try:
        # Determine paths
        if project_root is None:
            # Try to determine the project root
            script_path = Path(__file__).resolve()
            project_root = script_path.parent.parent.parent.parent.parent  # management folder
        
        apps_dir = project_root / "apps"
        old_app_dir = apps_dir / old_name
        new_app_dir = apps_dir / new_name
        
        # Validate names
        if not old_name.isalnum() or not new_name.isalnum():
            print("Error: App names should be alphanumeric")
            return 1
            
        # Check for reserved app names
        RESERVED_APP_NAMES = ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']
        if new_name.lower() in RESERVED_APP_NAMES:
            print(f"Error: '{new_name}' is a reserved name used by Django's built-in apps.")
            print("Please choose a different name.")
            return 1
            
        # Check if old app exists
        if not old_app_dir.exists():
            print(f"Error: App '{old_name}' does not exist at {old_app_dir}")
            return 1
            
        # Check if it's a Django app
        if not (old_app_dir / "apps.py").exists():
            print(f"Error: The directory '{old_app_dir}' does not appear to be a Django app (no apps.py found)")
            return 1
            
        # Check if new app name already exists
        if new_app_dir.exists():
            print(f"Error: App '{new_name}' already exists at {new_app_dir}")
            return 1
            
        # Ask for confirmation
        if not force:
            print(f"WARNING: You are about to rename app '{old_name}' to '{new_name}'")
            confirm = input("Are you sure you want to proceed? [y/N]: ")
            if confirm.lower() != "y":
                print("App renaming cancelled.")
                return 0
                
        # Update files within the app
        try:
            # Walk through all Python files in the app
            for root, dirs, files in os.walk(old_app_dir):
                for file in files:
                    if file.endswith(".py"):
                        file_path = Path(root) / file
                        content = file_path.read_text()
                        
                        # Replace imports and references
                        updated_content = (
                            content.replace(f"apps.{old_name}", f"apps.{new_name}")
                            .replace(f"from {old_name} import", f"from {new_name} import")
                            .replace(f"from {old_name}.", f"from {new_name}.")
                            .replace(f"app_name = '{old_name}'", f"app_name = '{new_name}'")
                            .replace(f'app_name = "{old_name}"', f'app_name = "{new_name}"')
                        )
                        
                        if content != updated_content:
                            file_path.write_text(updated_content)
                            print(f"Updated references in {file_path}")
        except Exception as e:
            print(f"Error updating app references: {e}")
            return 1
            
        # Update URLs
        try:
            base_urls_file = apps_dir / "config" / "urls" / "base.py"
            if base_urls_file.exists():
                content = base_urls_file.read_text()
                
                # Prepare replacement mapping
                replacements = [
                    (f'path("{old_name}/', f'path("{new_name}/'),
                    (f"path('{old_name}/'", f"path('{new_name}/'"),
                    (f'include("apps.{old_name}', f'include("apps.{new_name}'),
                    (f"include('apps.{old_name}", f"include('apps.{new_name}"),
                    (f'namespace="{old_name}"', f'namespace="{new_name}"'),
                    (f"namespace='{old_name}'", f"namespace='{new_name}'"),
                ]
                
                # Apply all replacements
                for old, new in replacements:
                    content = content.replace(old, new)
                    
                # Write updated content
                base_urls_file.write_text(content)
                print(f"Updated URL configuration in {base_urls_file}")
        except Exception as e:
            print(f"Warning: Could not update URL configuration: {e}")
            print("Continuing with app renaming anyway...")
            
        # Update settings
        try:
            settings_file = apps_dir / "config" / "settings" / "base.py"
            if settings_file.exists():
                content = settings_file.read_text()
                old_app_path = f'"apps.{old_name}"'
                new_app_path = f'"apps.{new_name}"'
                
                # Replace the app name in INSTALLED_APPS
                if old_app_path in content:
                    content = content.replace(old_app_path, new_app_path)
                    settings_file.write_text(content)
                    print(f"Updated app name in settings file: {settings_file}")
                else:
                    print(f"App '{old_name}' not explicitly listed in settings")
        except Exception as e:
            print(f"Warning: Could not update settings: {e}")
            
        # Update migrations in database
        try:
            # This would normally use Django's connection, 
            # but in standalone mode we'd need to connect directly
            print("Note: Migration records in database not updated in standalone mode")
            print("Run the command through Django to update migration records")
        except Exception as e:
            print(f"Warning: Could not update migrations in database: {e}")
            
        # Copy old app to new location with new name
        try:
            shutil.copytree(old_app_dir, new_app_dir)
            print(f"Created new app at {new_app_dir}")
        except Exception as e:
            print(f"Error creating new app directory: {e}")
            return 1
            
        # Remove old app directory
        try:
            shutil.rmtree(old_app_dir)
            print(f"Removed old app directory at {old_app_dir}")
        except Exception as e:
            print(f"Warning: Error removing old app directory: {e}")
            print("You may need to remove it manually.")
            
        print(f"Successfully renamed app from '{old_name}' to '{new_name}'")
        print("Note: You may need to restart your Django server for all changes to take effect")
        return 0
    except Exception as e:
        print(f"Error renaming app: {e}")
        return 1


# This allows the script to be run directly
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python renameapp.py old_app_name new_app_name [--force]")
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    force = "--force" in sys.argv
    
    sys.exit(rename_app_standalone(old_name, new_name, force))
