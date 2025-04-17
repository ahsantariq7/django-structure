"""
Custom management command to fix inconsistent migration history and related database issues.
"""

import os
import sys
import importlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.core.management import call_command
from django.apps import apps
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Fixes inconsistent migration history by analyzing and repairing dependency issues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force fixing migrations without confirmation",
        )
        parser.add_argument(
            "--fake-initial",
            action="store_true",
            help="Use --fake-initial flag when applying missing migrations",
        )
        parser.add_argument(
            "--fix-contenttypes",
            action="store_true",
            help="Fix stale content types",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        fake_initial = options["fake_initial"]
        fix_contenttypes = options["fix_contenttypes"]

        # Get connection
        self.connection = connection

        # Initialize migration loader
        self.loader = MigrationLoader(self.connection)

        # Check for issues
        self.stdout.write("Scanning for migration issues...")
        has_issues = False

        # 1. Dependency inconsistencies
        inconsistencies = self._find_inconsistencies()
        if inconsistencies:
            has_issues = True
            self.stdout.write(self.style.WARNING("\nFound migration inconsistencies:"))
            for applied, dependency in inconsistencies:
                self.stdout.write(
                    f"  - Migration {applied} is applied before its dependency {dependency}"
                )

        # 2. Ghost migrations (in DB but files missing)
        ghost_migrations = self._find_ghost_migrations()
        if ghost_migrations:
            has_issues = True
            self.stdout.write(
                self.style.WARNING("\nFound ghost migrations (in DB but files missing):")
            )
            for app, name in ghost_migrations:
                self.stdout.write(f"  - {app}.{name}")

        # 3. Missing migrations (files exist but not in DB)
        missing_migrations = self._find_missing_migrations()
        if missing_migrations:
            has_issues = True
            self.stdout.write(
                self.style.WARNING("\nFound missing migrations (files exist but not in DB):")
            )
            for app, name in missing_migrations:
                self.stdout.write(f"  - {app}.{name}")

        # 4. Stale content types
        stale_contenttypes = []
        if fix_contenttypes:
            stale_contenttypes = self._find_stale_contenttypes()
            if stale_contenttypes:
                has_issues = True
                self.stdout.write(self.style.WARNING("\nFound stale content types:"))
                for ct in stale_contenttypes:
                    self.stdout.write(f"  - {ct.app_label}.{ct.model} (id: {ct.id})")

        if not has_issues:
            self.stdout.write(self.style.SUCCESS("No migration issues found!"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry run - no changes will be made."))
            self.stdout.write(self.style.WARNING("Run without --dry-run to fix these issues."))
            return

        # Ask for confirmation
        if not force:
            self.stdout.write(
                self.style.WARNING(
                    "\nFixing migration issues may require database modifications. "
                    "This could result in data loss. MAKE A BACKUP FIRST!"
                )
            )
            confirm = input("Are you sure you want to proceed? [y/N]: ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.SUCCESS("Migration fix cancelled."))
                return

        # Fix each type of issue
        self.stdout.write(self.style.NOTICE("\nFixing migration issues..."))

        # 1. Fix inconsistencies
        if inconsistencies:
            self._fix_inconsistencies(inconsistencies)

        # 2. Fix ghost migrations
        if ghost_migrations:
            self._fix_ghost_migrations(ghost_migrations)

        # 3. Fix missing migrations
        if missing_migrations and not dry_run:
            self._fix_missing_migrations(missing_migrations, fake_initial)

        # 4. Fix stale content types
        if fix_contenttypes and stale_contenttypes:
            self._fix_stale_contenttypes(stale_contenttypes)

        self.stdout.write(self.style.SUCCESS("\nMigration issues have been fixed!"))

    def _find_inconsistencies(self):
        """Find inconsistencies in migration history"""
        inconsistencies = []
        recorder = MigrationRecorder(self.connection)
        applied = recorder.applied_migrations()

        for app_label, migration_name in applied:
            migration_key = (app_label, migration_name)
            if migration_key not in self.loader.graph.nodes:
                continue  # Skip migrations that aren't loaded

            node = self.loader.graph.nodes[migration_key]

            for parent in self.loader.graph.node_map[migration_key].parents:
                if parent not in applied:
                    inconsistencies.append((migration_key, parent))

        return inconsistencies

    def _find_ghost_migrations(self):
        """Find migrations in the database that don't have corresponding files"""
        ghost_migrations = []
        recorder = MigrationRecorder(self.connection)
        applied = recorder.applied_migrations()

        for app_label, migration_name in applied:
            migration_key = (app_label, migration_name)
            if migration_key not in self.loader.graph.nodes:
                ghost_migrations.append(migration_key)

        return ghost_migrations

    def _find_missing_migrations(self):
        """Find migrations that exist as files but aren't in the database"""
        missing_migrations = []
        recorder = MigrationRecorder(self.connection)
        applied = recorder.applied_migrations()

        # Get all migrations from disk
        for key in self.loader.graph.nodes:
            if key not in applied and key[0] != "contenttypes" and key[1] != "__first__":
                # Skip dependencies that don't exist in the app's directories
                try:
                    self.loader.get_migration_by_prefix(key[0], key[1])
                    missing_migrations.append(key)
                except ValueError:
                    pass

        return missing_migrations

    def _find_stale_contenttypes(self):
        """Find content types for models that no longer exist"""
        stale_contenttypes = []

        try:
            for ct in ContentType.objects.all():
                model_exists = False
                try:
                    model_class = apps.get_model(ct.app_label, ct.model)
                    model_exists = True
                except LookupError:
                    pass

                if not model_exists:
                    stale_contenttypes.append(ct)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking content types: {e}"))

        return stale_contenttypes

    def _fix_inconsistencies(self, inconsistencies):
        """Fix the inconsistencies by manipulating the migration records"""
        # Group inconsistencies by dependency
        dependencies_to_fix = {}
        for applied, dependency in inconsistencies:
            if dependency not in dependencies_to_fix:
                dependencies_to_fix[dependency] = []
            dependencies_to_fix[dependency].append(applied)

        # Fix each dependency
        for dependency, applied_migrations in dependencies_to_fix.items():
            app, migration_name = dependency
            self.stdout.write(f"\nFixing dependency: {app}.{migration_name}")

            with connection.cursor() as cursor:
                # 1. First, temporarily remove the records for dependent migrations
                self.stdout.write(f"  Temporarily removing dependent migrations...")
                for applied in applied_migrations:
                    app_name, migration = applied
                    self.stdout.write(f"    - Removing {app_name}.{migration}")
                    cursor.execute(
                        "DELETE FROM django_migrations WHERE app = %s AND name = %s",
                        [app_name, migration],
                    )

                # 2. Add the dependency migration record
                self.stdout.write(f"  Adding missing dependency: {app}.{migration_name}")
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                    [app, migration_name],
                )

                # 3. Re-add the dependent migrations
                self.stdout.write(f"  Restoring dependent migrations...")
                for applied in applied_migrations:
                    app_name, migration = applied
                    self.stdout.write(f"    - Restoring {app_name}.{migration}")
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                        [app_name, migration],
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Fixed dependency chain for {app}.{migration_name}")
            )

    def _fix_ghost_migrations(self, ghost_migrations):
        """Remove migration records for migrations that don't exist"""
        self.stdout.write("\nRemoving ghost migration records...")

        with connection.cursor() as cursor:
            for app, name in ghost_migrations:
                self.stdout.write(f"  - Removing {app}.{name}")
                cursor.execute(
                    "DELETE FROM django_migrations WHERE app = %s AND name = %s",
                    [app, name],
                )

        self.stdout.write(
            self.style.SUCCESS(f"Removed {len(ghost_migrations)} ghost migration records")
        )

    def _fix_missing_migrations(self, missing_migrations, fake_initial=False):
        """Apply missing migrations that exist as files but aren't in the database"""
        self.stdout.write("\nApplying missing migrations...")

        # Group by app to apply all migrations for one app at once
        apps_to_migrate = {}
        for app, name in missing_migrations:
            if app not in apps_to_migrate:
                apps_to_migrate[app] = []
            apps_to_migrate[app].append(name)

        # Apply migrations for each app
        for app, migrations in apps_to_migrate.items():
            self.stdout.write(f"  Migrating {app}...")

            # Sort migrations to ensure correct order
            sorted_migrations = sorted(migrations)

            try:
                # Use migrate command to apply the migrations
                # If fake_initial is specified, use it for the first migration
                if fake_initial and sorted_migrations:
                    # First migration with fake-initial
                    first_migration = sorted_migrations[0]
                    self.stdout.write(f"    - Applying {app}.{first_migration} with --fake-initial")
                    call_command(
                        "migrate",
                        app,
                        first_migration,
                        fake_initial=True,
                        verbosity=0,
                    )

                    # Rest of the migrations without fake-initial
                    for migration in sorted_migrations[1:]:
                        self.stdout.write(f"    - Applying {app}.{migration}")
                        call_command(
                            "migrate",
                            app,
                            migration,
                            verbosity=0,
                        )
                else:
                    # Apply all migrations for this app
                    call_command(
                        "migrate",
                        app,
                        verbosity=1,
                    )

                self.stdout.write(self.style.SUCCESS(f"  Successfully migrated {app}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error migrating {app}: {e}"))

    def _fix_stale_contenttypes(self, stale_contenttypes):
        """Remove content types for models that no longer exist"""
        self.stdout.write("\nRemoving stale content types...")

        for ct in stale_contenttypes:
            self.stdout.write(f"  - Removing {ct.app_label}.{ct.model} (id: {ct.id})")
            try:
                ct.delete()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error removing content type: {e}"))

        self.stdout.write(
            self.style.SUCCESS(f"Removed {len(stale_contenttypes)} stale content types")
        )


def fix_migrations_standalone(
    dry_run=False, force=False, fake_initial=False, fix_contenttypes=False
):
    """Standalone function to fix migrations without requiring full Django to start"""
    try:
        print("Analyzing migration history...")

        # This needs Django to be set up, so we'll just call the command directly
        from django.core.management import call_command

        call_command(
            "fixmigrations",
            dry_run=dry_run,
            force=force,
            fake_initial=fake_initial,
            fix_contenttypes=fix_contenttypes,
        )
        return 0
    except Exception as e:
        print(f"Error fixing migrations: {e}")
        return 1


# This allows the script to be run directly
if __name__ == "__main__":
    if "--help" in sys.argv:
        print(
            "Usage: python fixmigrations.py [--dry-run] [--force] [--fake-initial] [--fix-contenttypes]"
        )
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    fake_initial = "--fake-initial" in sys.argv
    fix_contenttypes = "--fix-contenttypes" in sys.argv

    sys.exit(fix_migrations_standalone(dry_run, force, fake_initial, fix_contenttypes))
