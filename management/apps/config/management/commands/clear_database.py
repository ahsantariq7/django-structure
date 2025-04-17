"""
Custom management command to clear the database by dropping all tables.
"""

import os
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = "Removes all tables from the database (WARNING: Destructive operation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force clearing without confirmation",
        )
        parser.add_argument(
            "--preserve-migrations",
            action="store_true",
            help="Preserve django_migrations table",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Truncate tables instead of dropping them",
        )
        parser.add_argument(
            "--standalone",
            action="store_true",
            help="Run in standalone mode without full Django initialization",
        )

    def handle(self, *args, **options):
        force = options["force"]
        preserve_migrations = options["preserve_migrations"]
        truncate = options["truncate"]
        standalone = options["standalone"]

        # If standalone mode is requested or we detect we're in a script
        if standalone or not hasattr(self, "stdout"):
            exit_code = clear_database_standalone(
                force=force,
                preserve_migrations=preserve_migrations,
                truncate=truncate,
                project_root=settings.BASE_DIR,
            )
            return exit_code

        # Standard Django command mode
        try:
            # Get database engine
            db_engine = connection.vendor

            # Get all tables in the database
            tables = self._get_tables()

            if not tables:
                self.stdout.write(self.style.SUCCESS("No tables found in the database."))
                return

            # Ask for confirmation
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"You are about to PERMANENTLY DELETE {len(tables)} tables from your database!\n"
                        "This operation cannot be undone and will result in complete data loss."
                    )
                )
                confirm = input(
                    "Are you ABSOLUTELY sure you want to proceed? Type 'yes' to confirm: "
                )
                if confirm.lower() != "yes":
                    self.stdout.write(self.style.SUCCESS("Database clearing cancelled."))
                    return

            # Filter out migrations table if requested
            if preserve_migrations:
                tables = [t for t in tables if t != "django_migrations"]
                self.stdout.write("Preserving django_migrations table.")

            # Drop/truncate all tables
            if truncate:
                self._truncate_tables(tables, db_engine)
            else:
                self._drop_tables(tables, db_engine)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully {('truncated' if truncate else 'dropped')} {len(tables)} tables."
                )
            )

        except Exception as e:
            raise CommandError(f"Error clearing database: {e}")

    def _get_tables(self):
        """Get all tables in the database"""
        tables = []
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [
                    row[0]
                    for row in cursor.fetchall()
                    if row[0] != "sqlite_sequence" and not row[0].startswith("sqlite_")
                ]
            elif connection.vendor == "postgresql":
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public';"
                )
                tables = [row[0] for row in cursor.fetchall()]
            elif connection.vendor == "mysql":
                cursor.execute("SHOW TABLES;")
                tables = [row[0] for row in cursor.fetchall()]
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Database vendor '{connection.vendor}' not explicitly supported. "
                        "Attempting generic approach."
                    )
                )
                try:
                    cursor.execute(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = DATABASE();"
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                except:
                    raise CommandError(f"Unsupported database engine: {connection.vendor}")

        return tables

    def _drop_tables(self, tables, db_engine):
        """Drop all tables in the database"""
        with connection.cursor() as cursor:
            if db_engine == "postgresql":
                # Disable foreign key checks and drop all tables in a single transaction
                cursor.execute("SET session_replication_role = 'replica';")

                for table in tables:
                    self.stdout.write(f"Dropping table '{table}'...")
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

                cursor.execute("SET session_replication_role = 'origin';")

            elif db_engine == "mysql":
                # Disable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

                for table in tables:
                    self.stdout.write(f"Dropping table '{table}'...")
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`;")

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            else:  # SQLite or other
                for table in tables:
                    self.stdout.write(f"Dropping table '{table}'...")
                    cursor.execute(f"DROP TABLE IF EXISTS `{table}`;")

    def _truncate_tables(self, tables, db_engine):
        """Truncate all tables in the database instead of dropping them"""
        with connection.cursor() as cursor:
            if db_engine == "postgresql":
                # Disable triggers and truncate all tables in a single transaction
                cursor.execute("SET session_replication_role = 'replica';")

                for table in tables:
                    self.stdout.write(f"Truncating table '{table}'...")
                    cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')

                cursor.execute("SET session_replication_role = 'origin';")

            elif db_engine == "mysql":
                # Disable foreign key checks
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

                for table in tables:
                    self.stdout.write(f"Truncating table '{table}'...")
                    cursor.execute(f"TRUNCATE TABLE `{table}`;")

                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            else:  # SQLite or other
                for table in tables:
                    self.stdout.write(f"Truncating table '{table}'...")
                    cursor.execute(f"DELETE FROM `{table}`;")
                    # Reset SQLite sequences if possible
                    try:
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
                    except:
                        pass


def clear_database_standalone(
    force=False, preserve_migrations=False, truncate=False, project_root=None
):
    """Standalone function to clear database without requiring full Django initialization"""
    try:
        # Determine project root if not provided
        if project_root is None:
            script_path = Path(__file__).resolve()
            project_root = script_path.parent.parent.parent.parent.parent  # management folder

        # Try to set up minimal Django environment
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings.development")
        sys.path.insert(0, str(project_root))

        print("Initializing database connection...")

        # Ask for confirmation
        if not force:
            print("\nWARNING: You are about to PERMANENTLY DELETE all tables from your database!")
            print("This operation cannot be undone and will result in complete data loss.")
            confirm = input("Are you ABSOLUTELY sure you want to proceed? Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("Database clearing cancelled.")
                return 0

        try:
            import django

            django.setup()

            # Now we can import and use Django ORM
            from django.db import connection

            # Create a command instance and call the appropriate methods
            cmd = Command()
            cmd.stdout = sys.stdout  # Redirect output to console

            tables = cmd._get_tables()

            if not tables:
                print("No tables found in the database.")
                return 0

            print(f"Found {len(tables)} tables in the database.")

            # Filter out migrations table if requested
            if preserve_migrations:
                tables = [t for t in tables if t != "django_migrations"]
                print("Preserving django_migrations table.")

            # Drop/truncate all tables
            if truncate:
                cmd._truncate_tables(tables, connection.vendor)
                print(f"Successfully truncated {len(tables)} tables.")
            else:
                cmd._drop_tables(tables, connection.vendor)
                print(f"Successfully dropped {len(tables)} tables.")

            return 0

        except Exception as e:
            print(f"Error: {e}")
            return 1

    except Exception as e:
        print(f"Error clearing database: {e}")
        return 1


# This allows the script to be run directly
if __name__ == "__main__":
    if "--help" in sys.argv:
        print("Usage: python cleardatabase.py [--force] [--preserve-migrations] [--truncate]")
        sys.exit(1)

    force = "--force" in sys.argv
    preserve_migrations = "--preserve-migrations" in sys.argv
    truncate = "--truncate" in sys.argv

    sys.exit(clear_database_standalone(force, preserve_migrations, truncate))
