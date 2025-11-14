import pytz
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import ConfigurationMixin


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_field):
        if not email:
            raise ValueError(_("Users must have an email address"))

        user = self.model(email=self.normalize_email(email), **extra_field)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        with transaction.atomic():
            user = self.create_user(email=email, password=password)
            user.is_superuser = True
            user.save(using=self._db)

            return user


class User(AbstractBaseUser, PermissionsMixin, ConfigurationMixin):
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        SPANISH = "es", "Español"

    email = models.EmailField(_("Email"), unique=True)
    name = models.CharField(_("Name"), max_length=255, null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    # Account status
    is_email_verified = models.BooleanField(_("Email verified"), default=False)

    # Localization preferences
    language = models.CharField(
        _("Preferred Language"),
        max_length=2,
        choices=Language.choices,
        default=Language.SPANISH,
        help_text=_("User's preferred language for the interface"),
    )
    timezone = models.CharField(
        _("Timezone"),
        max_length=100,
        default="UTC",
        help_text=_("User's timezone identifier (e.g., 'America/New_York', 'Europe/Madrid')"),
    )

    USERNAME_FIELD = "email"
    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-name"]

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        """Only super users can login to the django admin"""
        return self.is_superuser

    def get_local_time(self, utc_datetime=None):
        """
        Convert UTC datetime to user's local timezone

        Args:
            utc_datetime: UTC datetime object. If None, uses current UTC time.

        Returns:
            Localized datetime object
        """
        if utc_datetime is None:
            utc_datetime = timezone.now()

        try:
            user_tz = pytz.timezone(self.timezone)
            return utc_datetime.astimezone(user_tz)
        except pytz.UnknownTimeZoneError:
            # Fallback to UTC if timezone is invalid
            return utc_datetime

    def localize_datetime(self, naive_datetime):
        """
        Localize a naive datetime to user's timezone

        Args:
            naive_datetime: Naive datetime object

        Returns:
            Timezone-aware datetime object in user's timezone
        """
        try:
            user_tz = pytz.timezone(self.timezone)
            return user_tz.localize(naive_datetime)
        except pytz.UnknownTimeZoneError:
            # Fallback to UTC if timezone is invalid
            utc_tz = pytz.UTC
            return utc_tz.localize(naive_datetime)

    def is_valid_timezone(self):
        """
        Check if the user's timezone is valid

        Returns:
            bool: True if timezone is valid, False otherwise
        """
        try:
            pytz.timezone(self.timezone)
            return True
        except pytz.UnknownTimeZoneError:
            return False

    @property
    def timezone_display(self):
        """Get a human-readable display name for the user's timezone"""
        if not self.is_valid_timezone():
            return f"{self.timezone} (Invalid)"

        try:
            tz = pytz.timezone(self.timezone)
            # Get the timezone name, e.g., "Europe/Madrid" -> "Madrid"
            if "/" in self.timezone:
                city = self.timezone.split("/")[-1].replace("_", " ")
                return city
            return self.timezone
        except:
            return self.timezone

    @property
    def language_display(self):
        """Get the display name for the user's language"""
        return self.get_language_display()
