"""
Base URL configuration for the project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse

from .api import api_urlpatterns


# Admin site customization
admin.site.site_header = "Management Portal"
admin.site.site_title = "Management Admin"
admin.site.index_title = "Administration"

urlpatterns = [

    # Admin interface
    path("admin/", admin.site.urls),
    # Include API URLs
    path("api/", include(api_urlpatterns)),
]

# Serve static/media files in development
if settings.DEBUG:
    # Serve static files during development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Enable Django Debug Toolbar if installed
    try:
        import debug_toolbar

        # Append debug toolbar to existing patterns
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

    # Enable Django Browser Reload if installed
    try:
        from django_browser_reload import urls as browser_reload_urls

        # Append browser reload to existing patterns
        urlpatterns = [
            path("__reload__/", include(browser_reload_urls)),
        ] + urlpatterns
    except ImportError:
        pass
