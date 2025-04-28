from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model with additional fields
    """

    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True, verbose_name=_("Profile Picture")
    )
    phone_number = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Phone Number")
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of Birth"))
    address = models.TextField(null=True, blank=True, verbose_name=_("Address"))
    bio = models.TextField(null=True, blank=True, verbose_name=_("Bio"))
    token_version = models.IntegerField(default=0, help_text=_("Used to invalidate all tokens"))
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_token_created = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.username

    def increment_token_version(self):
        """Increment the token version to invalidate all existing tokens"""
        self.token_version += 1
        self.save(update_fields=["token_version"])
        return self.token_version

    def generate_verification_token(self):
        self.email_verification_token = uuid.uuid4()
        self.save()
        return self.email_verification_token

    def generate_password_reset_token(self):
        """Generate a unique password reset token and set expiration"""
        # Generate a unique token
        token = uuid.uuid4()
        
        # Store token and expiration (24 hours from now)
        self.password_reset_token = token
        self.password_reset_token_created = timezone.now()
        self.save(update_fields=["password_reset_token", "password_reset_token_created"])
        
        return token

    def is_password_reset_token_valid(self, token):
        """Check if the password reset token is valid and not expired"""
        # Convert string token to UUID if needed
        if isinstance(token, str):
            try:
                token = uuid.UUID(token)
            except ValueError:
                return False
        
        # Check if token matches
        if self.password_reset_token != token:
            return False
        
        # Check if token is expired (24 hours)
        token_age = timezone.now() - self.password_reset_token_created
        if token_age.total_seconds() > 86400:  # 24 hours in seconds
            return False
        
        return True

    def clear_password_reset_token(self):
        """Clear the password reset token after it's been used"""
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.save(update_fields=["password_reset_token", "password_reset_token_created"])
