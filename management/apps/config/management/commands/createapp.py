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
    help = "Creates a Django app in the apps directory or a custom directory"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--register",
            action="store_true",
            help="Register the app in INSTALLED_APPS automatically",
        )
        parser.add_argument(
            "--directory",
            help="Custom directory to create the app in (relative to project root)",
            default=None,
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force creation even if directory exists",
        )

    def handle(self, **options):
        app_name = options["name"]
        custom_dir = options["directory"]
        force = options.get("force", False)

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

        # Determine where to create the app
        if custom_dir is None:
            # If no custom directory provided, ask if user wants a custom location
            use_custom = input("Create app in a custom directory instead of 'apps'? [y/N]: ")
            if use_custom.lower() == "y":
                custom_dir = input("Enter directory path (relative to project root): ")

        if custom_dir:
            # Create the app in a custom directory
            parent_dir = Path(settings.ROOT_DIR) / custom_dir

            # Create parent directory if it doesn't exist
            if not parent_dir.exists():
                confirm = input(f"Directory '{custom_dir}' doesn't exist. Create it? [Y/n]: ")
                if confirm.lower() not in ["", "y", "yes"]:
                    self.stdout.write(self.style.ERROR("App creation cancelled."))
                    return
                parent_dir.mkdir(parents=True)
                # Create __init__.py in each directory level
                current = parent_dir
                while current != settings.ROOT_DIR:
                    init_file = current / "__init__.py"
                    init_file.touch(exist_ok=True)
                    current = current.parent

            # Set target to the custom directory
            target = parent_dir / app_name

            # Convert filesystem path to Python module path (replace / with .)
            module_path = custom_dir.replace("/", ".").replace("\\", ".")
            if module_path.endswith("."):
                module_path = module_path[:-1]
            module_path = f"{module_path}.{app_name}"
        else:
            # Set target directory to be inside apps/
            target = Path(settings.APPS_DIR) / app_name
            module_path = f"apps.{app_name}"

        # Check if target directory already exists
        if target.exists() and not force:
            raise CommandError(f"Directory '{target}' already exists. Use --force to overwrite.")

        # Create the full target directory structure first
        target.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files in the directory structure
        if not custom_dir:
            Path(settings.APPS_DIR / "__init__.py").touch(exist_ok=True)

        options["directory"] = str(target)

        # Call the original startapp command
        super().handle(**options)

        # Fix the apps.py file to use the correct import path
        self._fix_apps_file(app_name, target, module_path)

        # Create URLs and views
        self._create_urls_file(app_name, target)
        self._enhance_views_file(app_name, target)

        # Register URLs in the main URL configuration
        self._register_urls(app_name, module_path)

        # Register in INSTALLED_APPS if requested or in a custom directory
        if options.get("register", False) or custom_dir:
            self._register_in_installed_apps(module_path)

        self.stdout.write(self.style.SUCCESS(f"App '{app_name}' created successfully in {target}!"))

        self.stdout.write(self.style.SUCCESS(f"Test URL created at /{app_name}/test/"))

        # Auto-discovery message
        self.stdout.write(self.style.SUCCESS(f"App registered as '{module_path}'."))

    def _fix_apps_file(self, app_name, target_dir, module_path):
        """Update the apps.py file to use the correct app name"""
        apps_file = target_dir / "apps.py"
        if apps_file.exists():
            content = apps_file.read_text()
            # Replace the default app name with the proper dotted path
            content = content.replace(f'name = "{app_name}"', f'name = "{module_path}"')
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
        """Add detailed API views to the views.py file with Swagger documentation"""
        views_file = target_dir / "views.py"

        if views_file.exists():
            # Keep the existing content
            content = views_file.read_text()

            # Define imports for DRF, Swagger, and rendering
            imports = """
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
"""

            # Add test views with Swagger documentation
            test_views = f"""

@extend_schema(
    tags=["{app_name}"],
    summary="Test API endpoint for {app_name}",
    description="This is a test API endpoint for the {app_name} app",
    responses={{200: {{'type': 'object', 'properties': {{'app': {{'type': 'string'}}, 'status': {{'type': 'string'}}, 'message': {{'type': 'string'}}}}}}}}
)
@api_view(['GET'])
def api_test_view(request):
    data = {{
        "app": "{app_name}",
        "status": "ok",
        "message": "This is a test API endpoint for the {app_name} app."
    }}
    return Response(data)

def index_view(request):
    \"\"\"Index view for {app_name} app.\"\"\"
    context = {{
        "app_name": "{app_name}",
        "message": "Welcome to the {app_name} app."
    }}
    return render(request, "base.html", context)

def test_view(request):
    \"\"\"Test view for {app_name} app.\"\"\"
    context = {{
        "app_name": "{app_name}",
        "message": "This is a test view for the {app_name} app."
    }}
    return render(request, "base.html", context)
"""

            # Check if we need to add the imports
            if "from drf_spectacular.utils import extend_schema" not in content:
                content = imports + content

            # Check if we need to add the test views
            if "@extend_schema" not in content and "def api_test_view" not in content:
                content += test_views
                views_file.write_text(content)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Enhanced views file with Swagger documentation at {views_file}"
                    )
                )

    def _register_urls(self, app_name, module_path):
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
                    app_import = f"path('{app_name}/', include('{module_path}.urls', namespace='{app_name}'))"

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
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"API endpoints are documented in Swagger UI at /api/docs/"
                            )
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

    def _register_in_installed_apps(self, module_path):
        """Add the app to INSTALLED_APPS in settings"""
        try:
            # First try to use the utility function if available
            try:
                from apps.config.utils.app_discovery import register_app

                if register_app(module_path):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Added '{module_path}' to INSTALLED_APPS using auto-discovery"
                        )
                    )
                    return
            except ImportError:
                pass  # Fall back to the manual method

            # Fall back to manually updating the settings file
            settings_file = settings.ROOT_DIR / "apps" / "config" / "settings" / "base.py"

            if settings_file.exists():
                content = settings_file.read_text()

                # Check if the app is already in INSTALLED_APPS
                if f"'{module_path}'" in content or f'"{module_path}"' in content:
                    self.stdout.write(
                        self.style.SUCCESS(f"App '{module_path}' already in INSTALLED_APPS")
                    )
                    return

                # First try to add to LOCAL_APPS if that section exists
                if "LOCAL_APPS = [" in content:
                    new_content = content.replace(
                        "LOCAL_APPS = [", f"LOCAL_APPS = [\n    '{module_path}',"
                    )
                    settings_file.write_text(new_content)
                    self.stdout.write(self.style.SUCCESS(f"Added '{module_path}' to LOCAL_APPS"))
                    return

                # If not, try CUSTOM_APPS
                if "CUSTOM_APPS = [" in content:
                    new_content = content.replace(
                        "CUSTOM_APPS = [", f"CUSTOM_APPS = [\n    '{module_path}',"
                    )
                    settings_file.write_text(new_content)
                    self.stdout.write(self.style.SUCCESS(f"Added '{module_path}' to CUSTOM_APPS"))
                    return

                # Finally fall back to INSTALLED_APPS directly
                if "INSTALLED_APPS = [" in content:
                    new_content = content.replace(
                        "INSTALLED_APPS = [", f"INSTALLED_APPS = [\n    '{module_path}',"
                    )
                    settings_file.write_text(new_content)
                    self.stdout.write(
                        self.style.SUCCESS(f"Added '{module_path}' to INSTALLED_APPS")
                    )
                    return

                self.stdout.write(
                    self.style.WARNING("Could not find appropriate section in settings to add app")
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not update INSTALLED_APPS: {e}"))
