"""
Custom management command to create a new Django app in the proper structure.
"""

import os
from pathlib import Path
from django.core.management.commands.startapp import Command as StartAppCommand
from django.conf import settings
from django.core.management.base import CommandError
import sys


class Command(StartAppCommand):
    help = "Creates a Django app in the apps directory"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--register",
            action="store_true",
            help="Register the app in INSTALLED_APPS automatically",
        )

    def handle(self, **options):
        app_name = options["name"]

        # Check for reserved app names
        RESERVED_APP_NAMES = [
            "admin",
            "auth",
            "contenttypes",
            "sessions",
            "messages",
            "staticfiles",
        ]
        if app_name.lower() in RESERVED_APP_NAMES:
            raise CommandError(
                f"'{app_name}' is a reserved name used by Django's built-in apps. "
                f"Please choose a different name."
            )

        # Also check if app name is a Python module name
        if app_name.lower() in sys.modules:
            raise CommandError(
                f"'{app_name}' is a Python module name. "
                f"Using it as an app name may cause conflicts. Please choose a different name."
            )

        # Set target directory to be inside apps/
        target = Path(settings.APPS_DIR) / app_name

        # Create the full target directory structure first
        target.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files in the directory structure
        Path(settings.APPS_DIR / "__init__.py").touch(exist_ok=True)

        options["directory"] = str(target)

        # Call the original startapp command
        super().handle(**options)

        # Fix the apps.py file to use the correct import path
        self._fix_apps_file(app_name, target)

        # Create URLs and views
        self._create_urls_file(app_name, target)
        self._enhance_views_file(app_name, target)

        # Register URLs in the main URL configuration
        self._register_urls(app_name)

        self.stdout.write(
            self.style.SUCCESS(f"App '{app_name}' created successfully in apps/{app_name}!")
        )

        self.stdout.write(self.style.SUCCESS(f"Test URL created at /{app_name}/test/"))

        # Auto-discovery should handle the app registration
        # since it's in the apps/ directory and has apps.py
        self.stdout.write(
            self.style.SUCCESS(
                "Your app will be automatically discovered by the app_discovery system."
            )
        )

    def _fix_apps_file(self, app_name, target_dir):
        """Update the apps.py file to use the correct app name"""
        apps_file = target_dir / "apps.py"
        if apps_file.exists():
            content = apps_file.read_text()
            # Replace the default app name with the proper dotted path
            content = content.replace(f'name = "{app_name}"', f'name = "apps.{app_name}"')
            apps_file.write_text(content)

    def _create_urls_file(self, app_name, target_dir):
        """Create a urls.py file with test endpoints"""
        urls_content = f'''"""
URL Configuration for {app_name} app.
"""
from django.urls import path
from . import views

app_name = "{app_name}"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("test/", views.test_view, name="test"),
    path("api/test/", views.api_test_view, name="api_test"),
]
'''
        urls_file = target_dir / "urls.py"
        urls_file.write_text(urls_content)
        self.stdout.write(self.style.SUCCESS(f"Created URLs file at {urls_file}"))

    def _enhance_views_file(self, app_name, target_dir):
        """Add test views to the views.py file"""
        views_file = target_dir / "views.py"
        if views_file.exists():
            # Get existing content
            content = views_file.read_text()

            # Add imports if not already there
            if "from django.http import JsonResponse" not in content:
                content = (
                    "from django.http import JsonResponse\nfrom django.shortcuts import render\n"
                    + content
                )

            # Add test views
            test_views = f'''
def index_view(request):
    """Index view for {app_name} app."""
    data = {{
        "app": "{app_name}",
        "status": "ok",
        "message": "Welcome to the {app_name} API."
    }}
    return JsonResponse(data)

def test_view(request):
    """Test view for {app_name} app."""
    context = {{
        "app_name": "{app_name}",
        "message": "This is a test view for the {app_name} app."
    }}
    return render(request, "base.html", context)

def api_test_view(request):
    """API test view for {app_name} app."""
    data = {{
        "app": "{app_name}",
        "status": "ok",
        "message": "This is a test API endpoint for the {app_name} app."
    }}
    return JsonResponse(data)
'''
            # Add the test views to the file
            content += test_views
            views_file.write_text(content)
            self.stdout.write(self.style.SUCCESS(f"Enhanced views file at {views_file}"))

    def _register_urls(self, app_name):
        """Register the app's URLs in the main URL configuration"""
        try:
            # Locate the main URL configuration file
            base_urls_file = settings.ROOT_DIR / "apps" / "config" / "urls" / "base.py"

            if base_urls_file.exists():
                content = base_urls_file.read_text()

                # Check if the import for include is already there
                if "from django.urls import path" in content and "include" not in content:
                    content = content.replace(
                        "from django.urls import path", "from django.urls import path, include"
                    )

                # Check for namespace to avoid duplicate registrations
                namespace_pattern = f"namespace='{app_name}'"

                # Only proceed if the app namespace isn't already registered
                if namespace_pattern not in content:
                    app_import = f"path('{app_name}/', include('apps.{app_name}.urls', namespace='{app_name}'))"

                    # Process the file line by line to ensure we add to the right urlpatterns
                    lines = content.split("\n")
                    new_lines = []

                    # Find the main urlpatterns list (not inside conditional blocks)
                    in_main_urlpatterns = False
                    url_added = False

                    for line in lines:
                        # Detect the start of the main urlpatterns
                        if "urlpatterns = [" in line and not in_main_urlpatterns:
                            in_main_urlpatterns = True
                            # Add the app's URLs to the urlpatterns list
                            new_lines.append(line)
                            new_lines.append(f"    {app_import},")
                            url_added = True
                        else:
                            new_lines.append(line)

                    if url_added:
                        # Write the updated content back to the file
                        base_urls_file.write_text("\n".join(new_lines))
                        self.stdout.write(
                            self.style.SUCCESS(f"Registered {app_name} URLs in {base_urls_file}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Could not find main urlpatterns in {base_urls_file}"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{app_name} URLs already registered in {base_urls_file}"
                        )
                    )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not register URLs: {e}"))
