#!/usr/bin/env python
# management/removeapp.py - Wrapper script for the removeapp command

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Import the standalone function from the command
from apps.config.management.commands.removeapp import remove_app_standalone


def main():
    if len(sys.argv) < 2:
        print("Usage: python removeapp.py <app_name> [--force] [--keep-migrations]")
        return 1

    app_name = sys.argv[1]
    force = "--force" in sys.argv
    keep_migrations = "--keep-migrations" in sys.argv

    # Run the standalone function
    return remove_app_standalone(
        app_name, force=force, keep_migrations=keep_migrations, project_root=current_dir
    )


if __name__ == "__main__":
    sys.exit(main())
