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


# Standalone function that can be called directly
def remove_app_standalone(app_name, force=False, keep_migrations=False, project_root=None):
    """Standalone function to remove an app without requiring Django to start"""
    try:
        # Determine paths
        if project_root is None:
            # Try to determine the project root
            script_path = Path(__file__).resolve()
            project_root = script_path.parent.parent.parent.parent.parent  # management folder

        apps_dir = project_root / "apps"
        app_dir = apps_dir / app_name

        # Check if app exists
        if not app_dir.exists():
            print(f"Error: App '{app_name}' does not exist at {app_dir}")
            return 1

        # Check if it's a Django app
        if not (app_dir / "apps.py").exists():
            print(
                f"Error: The directory '{app_dir}' does not appear to be a Django app (no apps.py found)"
            )
            return 1

        # Ask for confirmation
        if not force:
            print(f"WARNING: You are about to completely remove the app '{app_name}' at {app_dir}")
            confirm = input("Are you sure you want to proceed? [y/N]: ")
            if confirm.lower() != "y":
                print("App removal cancelled.")
                return 0

        # Fix createapp.py if needed
        try:
            createapp_path = apps_dir / "config" / "management" / "commands" / "createapp.py"
            if createapp_path.exists():
                content = createapp_path.read_text()
                if "a\n        if apps_file.exists():" in content:
                    fixed_content = content.replace(
                        "a\n        if apps_file.exists():",
                        'apps_file = target_dir / "apps.py"\n        if apps_file.exists():',
                    )
                    createapp_path.write_text(fixed_content)
                    print("Fixed syntax error in createapp.py")
        except Exception as e:
            print(f"Warning: Could not fix createapp.py: {e}")

        # Remove migrations from database if requested
        if not keep_migrations:
            try:
                # Only import Django DB if possible
                print("Removing migration records...")

                # Try to set up minimal Django environment
                os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.development")
                sys.path.insert(0, str(project_root))

                db_success = False

                # Try using Django ORM if possible
                try:
                    import django

                    django.setup()

                    # Get database configuration
                    from django.conf import settings

                    db_config = settings.DATABASES.get("default", {})
                    db_engine = db_config.get("ENGINE", "")

                    # Try with Django connection
                    try:
                        from django.db import connection

                        with connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM django_migrations WHERE app = %s", [app_name]
                            )
                            deleted_count = cursor.rowcount
                            print(
                                f"Removed {deleted_count} migration records from django_migrations table"
                            )
                            db_success = True
                    except Exception as db_error:
                        print(f"Could not use Django DB connection: {db_error}")
                except Exception as e:
                    print(f"Could not configure Django: {e}")

                # Fallback to direct database connection if Django ORM failed
                if not db_success:
                    # Try SQLite first as it's simpler
                    try:
                        import sqlite3

                        db_path = project_root / "db.sqlite3"
                        if db_path.exists():
                            print("Attempting SQLite connection...")
                            conn = sqlite3.connect(str(db_path))
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM django_migrations WHERE app = ?", (app_name,)
                            )
                            deleted_count = cursor.rowcount
                            conn.commit()
                            conn.close()
                            print(f"Removed {deleted_count} migration records from SQLite database")
                            db_success = True
                    except Exception as sqlite_error:
                        print(f"SQLite fallback failed: {sqlite_error}")

                    # Try PostgreSQL if SQLite failed and we have psycopg2
                    if not db_success:
                        try:
                            import psycopg2

                            # Try to get connection info from environment or use defaults
                            db_name = os.environ.get("DB_NAME", "postgres")
                            db_user = os.environ.get("DB_USER", "postgres")
                            db_password = os.environ.get("DB_PASSWORD", "")
                            db_host = os.environ.get("DB_HOST", "localhost")
                            db_port = os.environ.get("DB_PORT", "5432")

                            print(f"Attempting PostgreSQL connection to {db_host}:{db_port}...")
                            conn = psycopg2.connect(
                                dbname=db_name,
                                user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port,
                            )
                            conn.autocommit = True
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM django_migrations WHERE app = %s", (app_name,)
                            )
                            deleted_count = cursor.rowcount
                            cursor.close()
                            conn.close()
                            print(
                                f"Removed {deleted_count} migration records from PostgreSQL database"
                            )
                        except ImportError:
                            print("psycopg2 not installed, skipping PostgreSQL direct connection")
                        except Exception as pg_error:
                            print(f"PostgreSQL fallback failed: {pg_error}")
            except Exception as e:
                print(f"Warning: Could not remove migration records: {e}")
                print("Continuing with app removal anyway...")

        # Remove the app directory
        try:
            shutil.rmtree(app_dir)
            print(f"Successfully removed app directory {app_dir}")
        except Exception as e:
            print(f"Error removing app directory: {e}")
            return 1

        # Try to update settings.py if it manually lists the app
        try:
            settings_file = apps_dir / "config" / "settings" / "base.py"

            if settings_file.exists():
                content = settings_file.read_text()
                app_path = f'"apps.{app_name}"'

                # Only modify if it explicitly lists the app
                if app_path in content:
                    lines = content.splitlines()
                    new_lines = []

                    # Remove the app from installed apps
                    for line in lines:
                        if app_path not in line:
                            new_lines.append(line)
                        else:
                            print(f"Removed {app_path} from settings")

                    settings_file.write_text("\n".join(new_lines))
        except Exception as e:
            print(f"Warning: Could not update settings file: {e}")

        # Add URL removal functionality
        try:
            # After removing app directory and settings, also remove URLs
            base_urls_file = apps_dir / "config" / "urls" / "base.py"
            if base_urls_file.exists():
                content = base_urls_file.read_text()
                
                # Look for URL patterns with single or double quotes
                import_pattern = f'path("{app_name}/"'
                alt_pattern = f"path('{app_name}/'"
                
                # Process the file line by line
                lines = content.split("\n")
                filtered_lines = []
                removed = False
                
                for line in lines:
                    if (import_pattern in line or alt_pattern in line) and f"namespace='{app_name}'" in line:
                        removed = True
                        print(f"Removed URL configuration for {app_name}")
                        continue
                    filtered_lines.append(line)
                
                if removed:
                    # Write the updated content back to the file
                    base_urls_file.write_text("\n".join(filtered_lines))
                    print(f"Updated URL configuration in {base_urls_file}")
                else:
                    print(f"No URL patterns found for {app_name} in {base_urls_file}")
        except Exception as e:
            print(f"Warning: Could not remove URL patterns: {e}")
            print("Continuing with app removal anyway...")
        
        print(f"App '{app_name}' was completely removed from the project")
        print("Note: You may need to restart your Django server for all changes to take effect")
        return 0

    except Exception as e:
        print(f"Error removing app: {e}")
        return 1


class Command(BaseCommand):
    help = "Completely removes a Django app from the project"

    def add_arguments(self, parser):
        parser.add_argument("name", help="Name of the app to remove")
        parser.add_argument(
            "--keep-migrations",
            action="store_true",
            help="Do not remove migration records from django_migrations table",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force removal even if confirmation fails"
        )
        parser.add_argument(
            "--standalone",
            action="store_true",
            help="Run in standalone mode, bypassing Django's startup",
        )

    def _remove_urls(self, app_name):
        """Remove app URLs from the main URL configuration"""
        try:
            # Locate the main URL configuration file
            base_urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"

            if base_urls_file.exists():
                content = base_urls_file.read_text()

                # Look for the specific line that includes this app's URLs
                import_pattern = (
                    f'path("{app_name}/", include("apps.{app_name}.urls", namespace="{app_name}"))'
                )
                alt_pattern = (
                    f"path('{app_name}/', include('apps.{app_name}.urls', namespace='{app_name}'))"
                )

                # Process the file line by line to ensure we only remove the right line
                lines = content.split("\n")
                filtered_lines = []
                removed = False

                for line in lines:
                    if import_pattern in line or alt_pattern in line:
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

    def handle(self, *args, **options):
        app_name = options["name"]
        force = options["force"]
        keep_migrations = options["keep_migrations"]
        standalone = options["standalone"]

        # If standalone mode is requested or we detect we're in a script
        if standalone or not hasattr(self, "stdout"):
            # Run in standalone mode
            from django.conf import settings

            exit_code = remove_app_standalone(
                app_name,
                force=force,
                keep_migrations=keep_migrations,
                project_root=settings.BASE_DIR,
            )
            return exit_code

        # Standard Django command mode
        try:
            from django.conf import settings

            # Get path to app directory
            app_dir = Path(settings.APPS_DIR) / app_name

            # Check if app exists
            if not app_dir.exists():
                raise CommandError(f"App '{app_name}' does not exist at {app_dir}")

            # Check if it's a Django app
            if not (app_dir / "apps.py").exists():
                raise CommandError(
                    f"The directory '{app_dir}' does not appear to be a Django app (no apps.py found)"
                )

            # Ask for confirmation
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"You are about to completely remove the app '{app_name}' at {app_dir}"
                    )
                )
                confirm = input("Are you sure you want to proceed? [y/N]: ")
                if confirm.lower() != "y":
                    self.stdout.write(self.style.SUCCESS("App removal cancelled."))
                    return

            # Fix the createapp.py file if needed
            try:
                createapp_path = (
                    settings.APPS_DIR / "config" / "management" / "commands" / "createapp.py"
                )
                if createapp_path.exists():
                    content = createapp_path.read_text()
                    if "a\n        if apps_file.exists():" in content:
                        # Fix the syntax error
                        fixed_content = content.replace(
                            "a\n        if apps_file.exists():",
                            'apps_file = target_dir / "apps.py"\n        if apps_file.exists():',
                        )
                        createapp_path.write_text(fixed_content)
                        self.stdout.write(self.style.SUCCESS("Fixed syntax error in createapp.py"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not fix createapp.py: {e}"))

            # Remove migrations from database if requested
            if not keep_migrations:
                try:
                    from django.db import connection

                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app_name])
                        deleted_count = cursor.rowcount
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Removed {deleted_count} migration records from django_migrations table"
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Could not remove migration records: {e}")
                    )

            # Remove the app directory
            try:
                shutil.rmtree(app_dir)
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully removed app directory {app_dir}")
                )
            except Exception as e:
                raise CommandError(f"Error removing app directory: {e}")

            # Try to update settings file if it manually lists the app
            try:
                from apps.config.settings import ROOT_DIR

                settings_file = ROOT_DIR / "apps" / "config" / "settings" / "base.py"

                if settings_file.exists():
                    content = settings_file.read_text()
                    app_path = f'"apps.{app_name}"'

                    # Only modify file if it explicitly lists the app
                    if app_path in content:
                        lines = content.splitlines()
                        new_lines = []

                        # Remove the app from LOCAL_APPS if explicitly listed
                        for line in lines:
                            if app_path not in line:
                                new_lines.append(line)
                            else:
                                self.stdout.write(f"Removed {app_path} from settings")

                        settings_file.write_text("\n".join(new_lines))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not update settings file: {e}"))

            self.stdout.write(
                self.style.SUCCESS(f"App '{app_name}' was completely removed from the project")
            )
            self.stdout.write(
                self.style.WARNING(
                    "Note: You may need to restart your Django server for all changes to take effect"
                )
            )

            # Call _remove_urls after app directory is removed
            self._remove_urls(app_name)

        except ImportError:
            # If Django settings can't be imported, run in standalone mode
            exit_code = remove_app_standalone(
                app_name, force=force, keep_migrations=keep_migrations
            )
            return exit_code


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
