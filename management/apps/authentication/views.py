from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
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
        user = serializer.save()

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

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(access_token),
            },
            status=status.HTTP_201_CREATED,
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
