from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
from teams.models import User

class leads(models.Model):

    company_name = models.CharField(_("Company Name"), max_length=150, blank=False, null=False)
    address1 = models.CharField(_("Address Line 1"), max_length=255, blank=False, null=False)
    address2 = models.CharField(_("Address Line 2"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=False, null=False)
    state = models.CharField(_("State"), max_length=255, blank=False, null=False)
    country = models.CharField(_("Country"), max_length=255, blank=False, null=False)
    pincode = models.CharField(_("Pin Code"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)
    user = models.IntegerField(_("User Id"))

    @property
    def user_id(self):
        return User.objects.get(pk=self.user)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return self.company_name
    