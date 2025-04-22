"""
API URL configuration for the project.
"""

from django.urls import path, include

# Define the API URL patterns
api_urlpatterns = [
    # API versioning
    # path('v1/', include('apps.config.urls.api_v1')),
    # API authentication
    path("auth/", include("rest_framework.urls")),
]

# Add JWT authentication endpoints
try:
    from apps.authentication.views import (
        TokenVerifyView,
        TokenRefreshView,
    )

    api_urlpatterns += [
        path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
        path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    ]
except ImportError:
    pass

# Add drf-spectacular documentation endpoints
try:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )

    api_urlpatterns += [
        # API schema and documentation
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
except ImportError:
    pass

# Create an __init__.py file to make the directory a package
urlpatterns = api_urlpatterns
