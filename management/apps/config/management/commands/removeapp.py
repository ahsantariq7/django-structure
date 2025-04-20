"""
Custom management command to completely remove a Django app.
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
    help = "Completely removes a Django app from the project"

    def add_arguments(self, parser):
        parser.add_argument("name", help="Name of the app to remove")
        parser.add_argument(
            "--force", action="store_true", help="Force removal without confirmation"
        )
        parser.add_argument(
            "--keep-migrations", action="store_true", help="Keep database migrations"
        )
        parser.add_argument(
            "--directory",
            help="Custom directory where the app is located (relative to project root)",
            default=None,
        )

    def handle(self, *args, **options):
        app_name = options["name"]
        force = options.get("force", False)
        keep_migrations = options.get("keep_migrations", False)
        custom_dir = options.get("directory", None)

        # Determine the app's location
        if custom_dir:
            # Use the provided custom directory
            app_dir = Path(settings.ROOT_DIR) / custom_dir / app_name
            module_path = f"{custom_dir.replace('/', '.')}.{app_name}"
        else:
            # Try to find the app in the apps directory first
            app_dir = Path(settings.APPS_DIR) / app_name
            module_path = f"apps.{app_name}"

            # If app is not found in the default location, try to search for it
            if not app_dir.exists() or not (app_dir / "apps.py").exists():
                # Search for the app in other locations
                found = False

                # Check in apps subdirectories
                for directory in settings.APPS_DIR.glob("**/"):
                    if (directory / app_name).exists() and (
                        directory / app_name / "apps.py"
                    ).exists():
                        relative_path = directory.relative_to(settings.ROOT_DIR)
                        app_dir = directory / app_name
                        module_path = f"{str(relative_path).replace('/', '.')}.{app_name}"
                        found = True
                        self.stdout.write(
                            self.style.WARNING(
                                f"App '{app_name}' found in custom location: {app_dir}"
                            )
                        )
                        break

                if not found:
                    raise CommandError(
                        f"App '{app_name}' does not exist or could not be found in project."
                    )

        # Check if it's a Django app
        if not (app_dir / "apps.py").exists():
            raise CommandError(
                f"The directory '{app_dir}' does not appear to be a Django app (no apps.py found)"
            )

        # Ask for confirmation
        if not force:
            self.stdout.write(
                self.style.WARNING(
                    f"You are about to completely remove app '{app_name}' from '{app_dir}'"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "This will delete all files and may remove database tables if migrate is run"
                )
            )
            confirm = input("Are you sure you want to proceed? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.SUCCESS("App removal cancelled."))
                return

        # Remove the app from settings first
        self._remove_from_settings(module_path)

        # Remove the app's URLs from the main URL configuration
        self._remove_urls(app_name, module_path)

        # Remove migrations if requested
        if not keep_migrations:
            self._remove_migrations(app_name)

        # Finally, remove the app directory
        try:
            if app_dir.exists():
                shutil.rmtree(app_dir)
                self.stdout.write(self.style.SUCCESS(f"Removed app directory at {app_dir}"))
            else:
                self.stdout.write(self.style.WARNING(f"App directory at {app_dir} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error removing app directory: {e}"))

        self.stdout.write(
            self.style.SUCCESS(f"App '{app_name}' and its associated files have been removed")
        )
        self.stdout.write(
            self.style.WARNING(
                "Note: You may need to restart your Django server for all changes to take effect"
            )
        )

    def _remove_from_settings(self, module_path):
        """Remove the app from INSTALLED_APPS in settings"""
        try:
            # Find the settings file
            settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"
            
            if settings_file.exists():
                content = settings_file.read_text()
                
                # Check for both single and double quotes
                app_patterns = [f"'{module_path}'", f'"{module_path}"']
                
                # Process the file line by line
                lines = content.split("\n")
                new_lines = []
                removed = False
                
                for i, line in enumerate(lines):
                    # Check if this line contains our app
                    if any(pattern in line for pattern in app_patterns):
                        # Check if it's in any of the app lists
                        is_app_line = False
                        for app_list in ["LOCAL_APPS", "CUSTOM_APPS", "INSTALLED_APPS"]:
                            # Find where this app list starts in the content
                            app_list_pos = content.find(f"{app_list} = [")
                            if app_list_pos >= 0:
                                # Check if this line appears after the app list starts
                                line_pos = content.find(line)
                                if line_pos > app_list_pos and line_pos < content.find(
                                    "]", app_list_pos
                                ):
                                    is_app_line = True
                                    break
                        
                        if is_app_line:
                            removed = True
                            
                            # If this line has a closing bracket we need to preserve it
                            if "]" in line:
                                # Always add the closing bracket
                                new_lines.append("]")
                                
                                # If there was a comma in previous line and it's now the last item
                                if i > 0 and "," in lines[i-1] and new_lines:
                                    # Remove trailing comma from previous line if this was the last entry
                                    prev_line = new_lines[-1]
                                    if prev_line.strip().endswith(","):
                                        new_lines[-1] = prev_line.rstrip(",")
                        
                            self.stdout.write(
                                self.style.SUCCESS(f"Removed '{module_path}' from settings")
                            )
                            continue
                    
                    new_lines.append(line)
                
                if removed:
                    # Write the updated content back to the file
                    settings_file.write_text("\n".join(new_lines))
                    self.stdout.write(self.style.SUCCESS(f"Updated settings in {settings_file}"))
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"App '{module_path}' not found in any app lists in settings"
                        )
                    )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not update settings: {e}"))

    def _remove_urls(self, app_name, module_path):
        """Remove app URLs from the main URL configuration"""
        try:
            # Locate the main URL configuration file
            base_urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"

            if base_urls_file.exists():
                content = base_urls_file.read_text()

                # Look for the specific lines that include this app's URLs
                import_patterns = [
                    f'path("{app_name}/", include("{module_path}.urls", namespace="{app_name}"))',
                    f"path('{app_name}/', include('{module_path}.urls', namespace='{app_name}'))",
                ]

                # Process the file line by line to ensure we only remove the right line
                lines = content.split("\n")
                filtered_lines = []
                removed = False

                for line in lines:
                    if any(pattern in line for pattern in import_patterns):
                        removed = True
                        self.stdout.write(
                            self.style.SUCCESS(f"Removed URL configuration for {app_name}")
                        )
                        continue
                    filtered_lines.append(line)

                if removed:
                    # Write the updated content back to the file
                    base_urls_file.write_text("\n".join(filtered_lines))
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated URL configuration in {base_urls_file}")
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"No URL patterns found for {app_name} in {base_urls_file}"
                        )
                    )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not remove URL patterns: {e}"))

    def _remove_migrations(self, app_name):
        """Remove migration records from the database"""
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                # Check if django_migrations table exists
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='django_migrations'"
                )
                if cursor.fetchone()[0] == 0:
                    self.stdout.write(self.style.NOTICE("No migrations table found in database"))
                    return

                # Delete migration records for this app
                cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app_name])
                count = cursor.rowcount
                if count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"Removed {count} migration record(s) from database")
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(f"No migration records found for app '{app_name}'")
                    )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not remove migrations from database: {e}"))


def remove_app_standalone(
    app_name, force=False, keep_migrations=False, project_root=None, custom_dir=None
):
    """Standalone function to remove an app, can be called from scripts"""
    from django.conf import settings
    from pathlib import Path
    import shutil
    import re

    if project_root is None:
        project_root = Path(settings.ROOT_DIR)

    # Determine the app's location and module path
    if custom_dir:
        app_dir = project_root / custom_dir / app_name
        module_path = f"{custom_dir.replace('/', '.')}.{app_name}"
    else:
        # First try in the apps directory
        apps_dir = project_root / "apps"
        app_dir = apps_dir / app_name
        module_path = f"apps.{app_name}"

        # If not there, search in subdirectories of apps
        if not app_dir.exists() or not (app_dir / "apps.py").exists():
            found = False

            # Look in apps subdirectories
            for directory in apps_dir.glob("**/"):
                if (directory / app_name).exists() and (directory / app_name / "apps.py").exists():
                    rel_path = directory.relative_to(project_root)
                    app_dir = directory / app_name
                    module_path = f"{str(rel_path).replace('/', '.')}.{app_name}"
                    found = True
                    print(f"App '{app_name}' found in custom location: {app_dir}")
                    break

            if not found:
                print(
                    f"Error: App '{app_name}' not found. Please specify the correct path with --directory."
                )
                return 1

    # Safety check - only proceed if we really found the app
    if not (app_dir / "apps.py").exists():
        if not force:
            print(f"Error: Directory '{app_dir}' does not appear to be a Django app.")
            return 1

    # Remove app directory
    try:
        if app_dir.exists():
            if not force:
                confirm = input(
                    f"Are you sure you want to delete the app directory at {app_dir}? [y/N]: "
                )
                if confirm.lower() != "y":
                    print("App removal cancelled.")
                    return 1

            # Delete the app directory
            shutil.rmtree(app_dir)
            print(f"Removed app directory: {app_dir}")
    except Exception as e:
        print(f"Error removing app directory: {e}")
        return 1

    # Remove from settings
    try:
        # Find the settings file
        settings_file = project_root / "apps" / "config" / "settings" / "base.py"

        if settings_file.exists():
            with open(settings_file, "r") as f:
                content = f.read()

            # Find app in any app list section (LOCAL_APPS, CUSTOM_APPS, INSTALLED_APPS)
            app_patterns = [f"'{module_path}'", f'"{module_path}"']

            # Search through the content looking for the app in any app list
            lines = content.split("\n")
            new_lines = []
            app_found = False

            for i, line in enumerate(lines):
                # Check if this line contains our app
                if any(pattern in line for pattern in app_patterns):
                    # Now check if it's part of an app list
                    app_found = True

                    # If this line has a closing bracket we need to preserve it
                    if "]" in line:
                        # Always add the closing bracket
                        new_lines.append("]")
                        
                        # If there was a comma in previous line and it's now the last item
                        if i > 0 and "," in lines[i-1] and new_lines:
                            # Remove trailing comma from previous line if this was the last entry
                            prev_line = new_lines[-1]
                            if prev_line.strip().endswith(","):
                                new_lines[-1] = prev_line.rstrip(",")
                else:
                    new_lines.append(line)

            if app_found:
                with open(settings_file, "w") as f:
                    f.write("\n".join(new_lines))
                print(f"Removed '{module_path}' from settings")
    except Exception as e:
        print(f"Warning: Could not update settings: {e}")

    # Remove from URL configuration
    try:
        urls_file = project_root / "apps" / "config" / "urls" / "base.py"

        if urls_file.exists():
            with open(urls_file, "r") as f:
                content = f.read()

            # Look for URL patterns with this app
            patterns = [
                f'path("{app_name}/',
                f"path('{app_name}/",
                f'include("{module_path}.urls"',
                f"include('{module_path}.urls'",
            ]

            new_content = []
            url_found = False

            for line in content.split("\n"):
                if any(pattern in line for pattern in patterns):
                    url_found = True
                    continue
                new_content.append(line)

            if url_found:
                with open(urls_file, "w") as f:
                    f.write("\n".join(new_content))
                print(f"Removed URL configuration for {app_name}")
    except Exception as e:
        print(f"Warning: Could not update URL configuration: {e}")

    # Remove migrations if not keeping them
    if not keep_migrations:
        try:
            migrations_dir = project_root / "apps" / "core" / "migrations"

            if migrations_dir.exists():
                migration_pattern = re.compile(r"^\d{4}_.*_{0}.*\.py$".format(app_name))
                for migration_file in migrations_dir.glob("*.py"):
                    if migration_pattern.match(migration_file.name):
                        migration_file.unlink()
                        print(f"Removed migration: {migration_file}")
        except Exception as e:
            print(f"Warning: Could not clean up migrations: {e}")

    print("App removal completed.")
    print("Note: You may need to restart your Django server for all changes to take effect")
    return 0


# Allow direct execution of this file
if __name__ == "__main__":
    # Execute the standalone function if run directly
    app_name = sys.argv[1] if len(sys.argv) > 1 else None
    force = "--force" in sys.argv
    keep_migrations = "--keep-migrations" in sys.argv

    if not app_name:
        print("Error: App name is required")
        print("Usage: python removeapp.py <app_name> [--force] [--keep-migrations]")
        sys.exit(1)

    sys.exit(remove_app_standalone(app_name, force=force, keep_migrations=keep_migrations))
