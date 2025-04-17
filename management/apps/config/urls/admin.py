"""
Admin URL configuration.

This module contains URL patterns specifically for the admin interface,
including any custom admin views.
"""

from django.contrib import admin
from django.urls import path

# URL patterns specific to admin functionality
admin_urlpatterns = [
    # Custom admin views can be added here
    # Example: path("report/", admin_views.report_view, name="admin-report"),
]

# Admin site customization
admin.site.site_header = "Management Admin"
admin.site.site_title = "Management Portal"
admin.site.index_title = "Dashboard"
