from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions


# Import API URLs
from apps.config.urls.api import api_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    # Include API URLs
    path("api/", include(api_urlpatterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
