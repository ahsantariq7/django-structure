from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from datetime import datetime, date

User = get_user_model()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "User Example",
            value={
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "profile_picture": "https://example.com/profile.jpg",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01",
                "address": "123 Main St, City, Country",
                "bio": "Software developer with 5 years of experience",
                "date_joined": "2023-01-01T00:00:00Z",
                "last_login": "2023-01-02T00:00:00Z",
                "is_active": True,
            },
        )
    ]
)
class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model with nested profile data"""

    date_of_birth = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_picture",
            "phone_number",
            "date_of_birth",
            "address",
            "bio",
            "date_joined",
            "last_login",
            "is_active",
        )
        read_only_fields = ("id", "date_joined", "last_login")
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value

    def validate_phone_number(self, value):
        """Basic phone number validation"""
        if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(_("Please enter a valid phone number."))
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Registration Example",
            value={
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePassword123!",
                "password_confirm": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "profile_picture": None,
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01",
                "address": "123 Main St, City, Country",
                "bio": "Software developer with 5 years of experience",
            },
        )
    ]
)
class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation"""

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    date_of_birth = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "profile_picture",
            "phone_number",
            "date_of_birth",
            "address",
            "bio",
        )
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        """Validate all fields before saving"""
        # Validate passwords match and meet requirements
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )

        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        # Validate username uniqueness
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError(
                {"username": _("A user with that username already exists.")}
            )

        # Validate email uniqueness
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": _("A user with this email already exists.")}
            )

        # Validate date_of_birth format if provided
        date_of_birth = attrs.get("date_of_birth")
        if date_of_birth:
            try:
                # If it's already a date object, it's valid
                if isinstance(date_of_birth, date):
                    return attrs

                # Try to parse the date string
                datetime.strptime(str(date_of_birth), "%Y-%m-%d").date()
            except ValueError:
                raise serializers.ValidationError(
                    {"date_of_birth": _("Invalid date format. Use YYYY-MM-DD.")}
                )

        # Validate profile picture if provided
        profile_picture = attrs.get("profile_picture")
        if profile_picture:
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise serializers.ValidationError(
                    {"profile_picture": _("Profile picture must be less than 5MB.")}
                )

            # Check file type
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
            if profile_picture.content_type not in allowed_types:
                raise serializers.ValidationError(
                    {"profile_picture": _("Only JPEG, PNG and GIF images are allowed.")}
                )

        return attrs

    def create(self, validated_data):
        """Create a new user with validated data"""
        # Remove password_confirm from validated data
        validated_data.pop("password_confirm")

        # Get the password and remove it from validated data
        password = validated_data.pop("password")

        # Create user instance but don't save yet
        user = User(**validated_data)

        # Set the password
        user.set_password(password)

        # Save the user
        user.save()

        return user


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Profile Update Example",
            value={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "profile_picture": None,
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01",
                "address": "123 Main St, City, Country",
                "bio": "Software developer with 5 years of experience",
            },
        )
    ]
)
class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    date_of_birth = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "phone_number",
            "date_of_birth",
            "address",
            "bio",
        )
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        """Ensure email is unique if changed"""
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Password Change Example",
            value={
                "old_password": "CurrentPassword123!",
                "new_password": "NewPassword123!",
                "new_password_confirm": "NewPassword123!",
            },
        )
    ]
)
class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate new password"""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Password fields didn't match.")}
            )

        try:
            validate_password(attrs["new_password"])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Token Verify Example",
            value={
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            },
        )
    ]
)
class TokenVerifySerializer(serializers.Serializer):
    """Serializer for token verification"""

    token = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate login credentials"""
        token = attrs.get("token")
        if not token:
            raise serializers.ValidationError(_("Token is required."))
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Token Refresh Example",
            value={
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            },
        )
    ]
)
class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""

    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate login credentials"""
        refresh = attrs.get("refresh")
        if not refresh:
            raise serializers.ValidationError(_("Refresh token is required."))
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Login Response Example",
            value={
                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "profile_picture": "https://example.com/profile.jpg",
                    "phone_number": "+1234567890",
                    "date_of_birth": "1990-01-01",
                    "address": "123 Main St, City, Country",
                    "bio": "Software developer with 5 years of experience",
                    "date_joined": "2023-01-01T00:00:00Z",
                    "last_login": "2023-01-02T00:00:00Z",
                    "is_active": True,
                },
            },
        )
    ]
)
class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Login Request Example",
            value={
                "username": "johndoe",
                "password": "SecurePassword123!",
            },
        )
    ]
)
class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Validate login credentials"""
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError(_("Please provide both username and password."))

        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Logout Request Example",
            value={
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            },
        )
    ]
)
class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""

    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate refresh token"""
        refresh = attrs.get("refresh")
        if not refresh:
            raise serializers.ValidationError(_("Refresh token is required."))
        return attrs
