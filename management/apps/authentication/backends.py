from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail import EmailMultiAlternatives

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to authenticate
    using either their username or email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Check if the username is an email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None


class CustomAccessToken(AccessToken):
    """Custom access token that includes user information and token version"""

    def verify(self, *args, **kwargs):
        """Verify the token and check token version"""
        super().verify(*args, **kwargs)

        # Get the user and token version
        user_id = self.payload.get("user_id")
        token_version = self.payload.get("token_version", 0)

        try:
            user = User.objects.get(id=user_id)
            user_version = user.token_version

            # Check if token version matches user's current version
            # If token version is less than user's version, the token is invalid
            if token_version < user_version:
                raise InvalidToken("Token version mismatch - user has logged out")

            # Check if token is blacklisted
            try:
                outstanding_token = OutstandingToken.objects.get(token=str(self))
                if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    raise InvalidToken("Token has been blacklisted")
            except OutstandingToken.DoesNotExist:
                pass

        except User.DoesNotExist:
            raise InvalidToken("User not found")


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that also checks if the token is blacklisted
    and if the token version matches the user's current token version.
    """

    def get_validated_token(self, raw_token):
        """
        Override the get_validated_token method to use our custom token class.
        """
        # Use our custom token class
        return CustomAccessToken(raw_token)


class DualEmailBackend:
    """
    Custom email backend that sends emails both via SMTP and to the console
    """

    def __init__(self, *args, **kwargs):
        self.smtp_backend = SMTPBackend(*args, **kwargs)
        self.console_backend = ConsoleBackend(*args, **kwargs)

    def send_messages(self, email_messages):
        # Send via SMTP
        smtp_result = self.smtp_backend.send_messages(email_messages)

        # Also send to console
        console_result = self.console_backend.send_messages(email_messages)

        return smtp_result  # Return SMTP result as primary result
