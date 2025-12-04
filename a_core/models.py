from django.db import models
from django.utils.translation import gettext_lazy as _

class LabelGroup(models.TextChoices):
    CATEGORY = "CATEGORY", _("Category")
    REPORT_TYPE = "REPORT_TYPE", _("Report type")


class BranchLabel(models.Model):

    branch = models.ForeignKey("teams.Branch", verbose_name=_("branch"), on_delete=models.CASCADE, related_name="branchlabels")
    group = models.CharField(_("group"), max_length=50, choices=LabelGroup.choices)
    key_value = models.CharField(_("key value"), max_length=50)
    label = models.CharField(_("label"), max_length=200)

    class Meta:
        db_table = "branchlabel"
        indexes = [
            models.Index(fields=["branch"]),
            models.Index(fields=["branch", "group"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "group", "key_value"],
                name='unique_branch_group_key_value'
            )
        ]

    def __str__(self):
        return f"{self.branch.branch_name} | {self.group} : {self.key_value} --> {self.label}"
    

class DocumentOwnerType(models.TextChoices):
    BILLER = "biller", _("Biller")
    BANK = "bank", _("Bank")
    CUSTOMER = "customer", _("Customer")
    OTHER = "other", _("Other")

class DocumentType(models.TextChoices):
    signature = "signature", _("Signature")
    stamp = "stamp", _("Stamp")
    gst = "gst", _("GST Certificate")
    msme = "msme", _("MSME Certificate")
    other = "other", _("Other")


class Documents(models.Model):
    owner_type = models.CharField(_("owner_type"), max_length=50, choices=DocumentOwnerType.choices)
    owner_id = models.PositiveIntegerField(_("owner_id"))
    doc_type = models.CharField(_("Document type"), max_length=50, choices=DocumentType.choices)
    file = models.FileField(_("file"), upload_to="")
    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)
    branch = models.ForeignKey("teams.Branch", verbose_name=_("branch"), on_delete=models.CASCADE, related_name="documents")

    class Meta:
        db_table = "documents"
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return f"{self.owner_type} - {self.owner_id} - {self.doc_type}"
    
    @property
    def is_image(self):
        return self.file.url.lower().endswith((".png", ".jpg", ".jpeg"))
    
    @property
    def is_pdf(self):
        return self.file.url.lower().endswith(".pdf")
    

