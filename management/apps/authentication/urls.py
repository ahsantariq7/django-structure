"""
URL Configuration for authentication app.
"""
from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("test/", views.test_view, name="test"),
    path("api/test/", views.api_test_view, name="api_test"),
]
