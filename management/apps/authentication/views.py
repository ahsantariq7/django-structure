from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
    inline_serializer,
)
from django.shortcuts import render
from rest_framework import status, generics, permissions, viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    TokenResponseSerializer,
    LoginSerializer,
    TokenVerifySerializer,
    TokenRefreshSerializer,
    LogoutSerializer,
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .backends import CustomAccessToken
from django.urls import reverse
from apps.config.utils.email.services import EmailService
from rest_framework import serializers

User = get_user_model()

# Create your views here.


@extend_schema(
    tags=["authentication"],
    summary="Test API endpoint for authentication",
    description="This is a test API endpoint for the authentication app",
    responses={
        200: {
            "type": "object",
            "properties": {
                "app": {"type": "string"},
                "status": {"type": "string"},
                "message": {"type": "string"},
            },
        }
    },
)
@api_view(["GET"])
def api_test_view(request):
    data = {
        "app": "authentication",
        "status": "ok",
        "message": "This is a test API endpoint for the authentication app.",
    }
    return Response(data)


def index_view(request):
    """Index view for authentication app."""
    context = {"app_name": "authentication", "message": "Welcome to the authentication app."}
    return render(request, "base.html", context)


def test_view(request):
    """Test view for authentication app."""
    context = {
        "app_name": "authentication",
        "message": "This is a test view for the authentication app.",
    }
    return render(request, "base.html", context)


@extend_schema(
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new user account with the provided information",
    request=UserCreateSerializer,
    responses={
        201: TokenResponseSerializer,
        400: OpenApiResponse(description="Bad Request - Invalid data provided"),
    },
)
class RegisterView(generics.CreateAPIView):
    """View for user registration"""

    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = serializer.save()
            print(f"User created successfully: {user.email}")

            # Generate verification token
            token = user.generate_verification_token()
            print(f"Verification token generated: {token}")

            # Create verification URL
            verify_url = request.build_absolute_uri(
                reverse("authentication:verify-email", kwargs={"token": token})
            )
            print(f"Verification URL created: {verify_url}")

            try:
                # Send verification email
                email_sent = EmailService.send_verification_email(user, verify_url)
                print(f"Email sending status: {'Success' if email_sent else 'Failed'}")

                if not email_sent:
                    print("Email sending failed, but user was created")
                    return Response(
                        {
                            "detail": "Account created but verification email failed to send. "
                            "Please use the resend verification endpoint."
                        },
                        status=status.HTTP_201_CREATED,
                    )

            except Exception as e:
                print(f"Error sending verification email: {str(e)}")
                return Response(
                    {
                        "detail": "Account created but verification email failed to send. "
                        "Please use the resend verification endpoint."
                    },
                    status=status.HTTP_201_CREATED,
                )

            print(f"Registration completed successfully for: {user.email}")
            return Response(
                {
                    "detail": "Registration successful. Please check your email to verify your account."
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print(f"Error during registration: {str(e)}")
            return Response(
                {"error": "Registration failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Login user",
    description="Authenticate user with username and password and return JWT tokens",
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        401: OpenApiResponse(description="Unauthorized - Invalid credentials"),
    },
)
class LoginView(TokenObtainPairView):
    """Custom login view that supports username and password login"""

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if not user:
            return Response(
                {"error": _("Invalid credentials.")}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.email_verified:
            return Response(
                {"error": _("Please verify your email address before logging in.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": _("User account is disabled.")}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Add custom claims to the token
        refresh["user_id"] = user.id
        refresh["username"] = user.username
        refresh["email"] = user.email
        refresh["first_name"] = user.first_name
        refresh["last_name"] = user.last_name
        refresh["token_version"] = user.token_version

        # Create a custom access token
        access_token = CustomAccessToken()
        access_token["user_id"] = user.id
        access_token["username"] = user.username
        access_token["email"] = user.email
        access_token["first_name"] = user.first_name
        access_token["last_name"] = user.last_name
        access_token["token_version"] = user.token_version

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(access_token),
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Logout user",
    description="Blacklist both refresh and access tokens to logout the user",
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description="Successfully logged out"),
        400: OpenApiResponse(description="Bad Request"),
    },
)
class LogoutView(APIView):
    """View for user logout"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                # Get the refresh token object
                token = RefreshToken(refresh_token)

                # Get the access token from the request header
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    access_token = auth_header.split(" ")[1]

                    # Blacklist both tokens
                    from rest_framework_simplejwt.token_blacklist.models import (
                        OutstandingToken,
                        BlacklistedToken,
                    )

                    # Blacklist refresh token
                    try:
                        refresh_outstanding = OutstandingToken.objects.get(token=refresh_token)
                        BlacklistedToken.objects.create(token=refresh_outstanding)
                    except OutstandingToken.DoesNotExist:
                        pass

                    # Blacklist access token
                    try:
                        access_outstanding = OutstandingToken.objects.get(token=access_token)
                        BlacklistedToken.objects.create(token=access_outstanding)
                    except OutstandingToken.DoesNotExist:
                        pass

                # Increment the user's token version to invalidate all existing tokens
                old_version = request.user.token_version
                new_version = request.user.increment_token_version()
                print(f"Token version incremented from {old_version} to {new_version}")

                return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
            return Response(
                {"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["User Management"],
    summary="User profile management",
    description="Retrieve and update user profile information",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Unauthorized"),
    },
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user profile management"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "put", "patch"]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Authentication"],
    summary="Change password",
    description="Change user password with old password verification",
    request=PasswordChangeSerializer,
    responses={
        200: OpenApiResponse(description="OK - Password successfully changed"),
        400: OpenApiResponse(description="Bad Request - Invalid data or wrong old password"),
    },
)
class PasswordChangeView(APIView):
    """View for changing user password"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"old_password": [_("Wrong password.")]}, status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response(
                {"message": _("Password successfully changed.")}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Request password reset",
    description="Send password reset email to the provided email address",
    request=OpenApiExample("Password Reset Request", value={"email": "john@example.com"}),
    responses={
        200: OpenApiResponse(description="OK - Password reset email sent"),
        400: OpenApiResponse(description="Bad Request - Email is required"),
    },
)
class PasswordResetRequestView(APIView):
    """View for requesting password reset"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"email": [_("Email is required.")]}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            # Here you would typically:
            # 1. Generate a password reset token
            # 2. Send an email with the reset link
            # 3. Store the token with an expiration time
            return Response(
                {"message": _("Password reset email has been sent.")}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"message": _("Password reset email has been sent.")}, status=status.HTTP_200_OK
            )


@extend_schema(
    tags=["Authentication"],
    summary="Confirm password reset",
    description="Reset password using the token received via email",
    request=OpenApiExample(
        "Password Reset Confirm",
        value={"token": "reset_token_here", "new_password": "NewPassword123!"},
    ),
    responses={
        200: OpenApiResponse(description="OK - Password has been reset successfully"),
        400: OpenApiResponse(description="Bad Request - Invalid token or missing data"),
    },
)
class PasswordResetConfirmView(APIView):
    """View for confirming password reset"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"message": _("Token and new password are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Here you would typically:
            # 1. Validate the token
            # 2. Get the user associated with the token
            # 3. Set the new password
            return Response(
                {"message": _("Password has been reset successfully.")}, status=status.HTTP_200_OK
            )
        except ValidationError:
            return Response(
                {"message": _("Invalid or expired token.")}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Token"],
    summary="Verify token",
    description="Verify if a token is valid",
    request=TokenVerifySerializer,
    responses={
        200: OpenApiResponse(description="OK - Token is valid"),
        401: OpenApiResponse(description="Unauthorized - Invalid token"),
    },
)
class TokenVerifyView(APIView):
    """View for token verification"""

    permission_classes = [permissions.AllowAny]
    serializer_class = TokenVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            # Verify the token
            AccessToken(token)
            return Response({"detail": _("Token is valid.")}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"error": _("Invalid token.")}, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    tags=["Token"],
    summary="Refresh token",
    description="Get a new access token using a refresh token",
    request=TokenRefreshSerializer,
    responses={
        200: TokenResponseSerializer,
        401: OpenApiResponse(description="Unauthorized - Invalid refresh token"),
    },
)
class TokenRefreshView(APIView):
    """View for token refresh"""

    permission_classes = [permissions.AllowAny]
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            # Create a new refresh token from the provided one
            refresh = RefreshToken(refresh_token)

            # Get the user from the token
            user_id = refresh.payload.get("user_id")
            user = User.objects.get(id=user_id)

            # Get the current token version from the refresh token
            token_version = refresh.payload.get("token_version", 0)

            # Verify that the token version matches the user's current version
            if token_version < user.token_version:
                raise InvalidToken("Token version mismatch - user has logged out")

            # Generate new tokens
            new_refresh = RefreshToken.for_user(user)

            # Add custom claims to the token
            new_refresh["user_id"] = user.id
            new_refresh["username"] = user.username
            new_refresh["email"] = user.email
            new_refresh["first_name"] = user.first_name
            new_refresh["last_name"] = user.last_name
            new_refresh["token_version"] = user.token_version

            # Create a custom access token
            access_token = CustomAccessToken()
            access_token["user_id"] = user.id
            access_token["username"] = user.username
            access_token["email"] = user.email
            access_token["first_name"] = user.first_name
            access_token["last_name"] = user.last_name
            access_token["token_version"] = user.token_version

            return Response(
                {
                    "user": UserSerializer(user).data,
                    "refresh": str(new_refresh),
                    "access": str(access_token),
                },
                status=status.HTTP_200_OK,
            )
        except (TokenError, InvalidToken, User.DoesNotExist):
            return Response(
                {"error": _("Invalid refresh token.")}, status=status.HTTP_401_UNAUTHORIZED
            )


@extend_schema(
    tags=["Authentication"],
    summary="Verify email address",
    description="Verify user's email address using the token sent via email",
    responses={
        200: OpenApiResponse(description="Email verified successfully"),
        400: OpenApiResponse(description="Invalid or expired token"),
    },
)
class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)

            if not user.email_verified:
                print(f"Verifying email for user: {user.email}")
                user.email_verified = True
                user.save()

                # Send welcome email
                try:
                    # Create login URL
                    login_url = request.build_absolute_uri("/auth/login")

                    # Send welcome email
                    email_sent = EmailService.send_welcome_email(user=user, login_url=login_url)

                    print(
                        f"Welcome email sending status for {user.email}: {'Success' if email_sent else 'Failed'}"
                    )

                except Exception as e:
                    print(f"Error sending welcome email to {user.email}: {str(e)}")

                return Response(
                    {"detail": "Email verified successfully. Welcome email has been sent."},
                    status=status.HTTP_200_OK,
                )

            print(f"Email already verified for user: {user.email}")
            return Response({"detail": "Email already verified."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            print(f"Invalid verification token: {token}")
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


# Add this serializer at the top with your other serializers
class EmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email address to resend verification link")


class ResendVerificationResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ResendVerificationErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


@extend_schema(
    tags=["Authentication"],
    summary="Resend verification email",
    description=(
        "Request a new email verification link. If the email exists and is not verified, "
        "a new verification link will be sent. For security reasons, the API returns a "
        "success message regardless of whether the email exists or not."
    ),
    request=EmailRequestSerializer,
    responses={
        200: OpenApiResponse(
            description="Request processed successfully",
            response=ResendVerificationResponseSerializer,
        ),
        400: OpenApiResponse(description="Bad Request", response=ResendVerificationErrorSerializer),
    },
    examples=[
        OpenApiExample(
            "Valid Request",
            summary="Example request with email",
            description="Send verification email request",
            value={"email": "user@example.com"},
            request_only=True,
        ),
        OpenApiExample(
            "Success Response",
            summary="Successful response",
            description="Email sent or account not found",
            value={
                "detail": "If an account exists with this email, a verification link will be sent."
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Already Verified Error",
            summary="Email already verified",
            description="Error when email is already verified",
            value={"error": "Email is already verified."},
            response_only=True,
            status_codes=["400"],
        ),
        OpenApiExample(
            "Missing Email Error",
            summary="Missing email field",
            description="Error when email is not provided",
            value={"error": "Email is required."},
            response_only=True,
            status_codes=["400"],
        ),
    ],
)
class ResendVerificationEmailView(APIView):
    """View for requesting a new verification email"""

    permission_classes = [permissions.AllowAny]
    serializer_class = EmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            print(f"Email verification request failed: Invalid data - {serializer.errors}")
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        print(f"Processing email verification request for: {email}")

        try:
            user = User.objects.get(email=email)

            # Check if email is already verified
            if user.email_verified:
                print(f"Email verification request failed: Email already verified - {email}")
                return Response(
                    {"error": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST
                )

            # Generate new verification token
            token = user.generate_verification_token()
            print(f"Generated new verification token for user: {user.username}")

            # Create verification URL
            verify_url = request.build_absolute_uri(
                reverse("authentication:verify-email", kwargs={"token": token})
            )
            print(f"Verification URL generated: {verify_url}")

            try:
                # Send new verification email
                email_sent = EmailService.send_verification_email(user, verify_url)

                if email_sent:
                    print(f"Verification email sent successfully to: {email}")
                    return Response(
                        {"detail": "Verification email sent successfully."},
                        status=status.HTTP_200_OK,
                    )
                else:
                    print(f"Failed to send verification email to: {email}")
                    return Response(
                        {"error": "Failed to send verification email. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            except Exception as e:
                print(f"Error sending verification email to {email}: {str(e)}")
                return Response(
                    {"error": "Failed to send verification email. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except User.DoesNotExist:
            print(f"Email verification request: User not found - {email}")
            # For security reasons, don't reveal if email exists
            return Response(
                {
                    "detail": "If an account exists with this email, a verification link will be sent."
                },
                status=status.HTTP_200_OK,
            )
