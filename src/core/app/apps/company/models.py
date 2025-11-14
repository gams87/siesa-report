import base64
import imghdr
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class Company(BaseModel):
    name = models.CharField(max_length=255, verbose_name=_("Nombre"))
    logo = models.ImageField(upload_to="company/logos/", null=True, blank=True, verbose_name=_("Logo"))
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("Teléfono"))
    email = models.EmailField(null=True, blank=True, verbose_name=_("Correo Electrónico"))
    is_default = models.BooleanField(default=False, verbose_name=_("Predeterminada"))

    class Meta:
        verbose_name = _("Compañía")
        verbose_name_plural = _("Compañías")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If this company is set as default, unset all other defaults
        if self.is_default:
            Company.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def get_logo_base64(self):
        """Convert logo to base64 string with format detection"""
        if not self.logo:
            return None, None

        try:
            with self.logo.open("rb") as logo_file:
                logo_data = logo_file.read()
                logo_base64 = base64.b64encode(logo_data).decode("utf-8")

                # Detect image format
                img_format = imghdr.what(None, h=logo_data) or "png"

                return logo_base64, img_format
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            return None, None

    def to_dict_for_pdf(self):
        """Returns a dictionary with company data ready for PDF generation"""
        data = {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
        }

        logo_base64, logo_format = self.get_logo_base64()
        if logo_base64:
            data["logo_base64"] = logo_base64
            data["logo_format"] = logo_format

        return data
