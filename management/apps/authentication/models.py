from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


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
