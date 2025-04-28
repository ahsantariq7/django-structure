"""
URL Configuration for authentication app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

app_name = "authentication"

# Create a router and register our viewset
router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")

urlpatterns = [
    # Authentication endpoints
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    # Password management
    path("password/change/", views.PasswordChangeView.as_view(), name="password_change"),
    path(
        "password/reset/", views.PasswordResetRequestView.as_view(), name="password_reset_request"
    ),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/page/",
        views.PasswordResetConfirmPageView.as_view(),
        name="password-reset-confirm-page",
    ),
    # Include router URLs
    path("", include(router.urls)),
    # Swagger URLs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/", SpectacularSwaggerView.as_view(url_name="authentication:schema"), name="swagger-ui"
    ),
    path("redoc/", SpectacularRedocView.as_view(url_name="authentication:schema"), name="redoc"),
    path("verify-email/<uuid:token>/", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification/",
        views.ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
]
