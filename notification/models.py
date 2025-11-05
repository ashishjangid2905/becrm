from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from django.utils.translation import gettext_lazy as _

class Notifications(models.Model):
    user = models.ForeignKey("teams.User", verbose_name=_("user"), on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField(_("message"))
    is_read = models.BooleanField(_("is read"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(_("object id"), null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    branch = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        target = f"{self.related_object}" if self.related_object else "General"
        return f"{self.user}: {target} - {self.message[:50]}"
    