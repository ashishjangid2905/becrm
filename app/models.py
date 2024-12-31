from django.db import models

# Create your models here.

from teams.models import User
from django.utils.translation import gettext_lazy as _

class ActivityLog(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(_("Action"), max_length=255)
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now=True)
    extra_info = models.JSONField(_("Extra Info"), null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} - {self.action} - {self.timestamp}'
    
    class Meta:
        verbose_name = 'ActivityLog'
        verbose_name_plural = 'ActivityLog'
        db_table = "ActivityLog"