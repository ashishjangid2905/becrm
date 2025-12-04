from django.db import models
from django.utils.translation import gettext_lazy as _
from invoice.utils import VARIABLES

# Create your models here.
class Biller(models.Model):
    biller_name = models.CharField(_("Biller Name"), max_length=150)
    brand_name = models.CharField(_("Brand Name"), max_length=150, null=True, blank=True)
    biller_gstin = models.CharField(_("Biller Gstin"), max_length=20, blank=True, null=True)
    biller_pan = models.CharField(_("Biller Pan"), max_length=15, blank=True, null=True)
    biller_msme = models.CharField(_("Biller MSME"), max_length=150, blank=True, null=True)
    reg_address1 = models.CharField(_("Reg. Address Line1"), max_length=254)
    reg_address2 = models.CharField(_("Reg. Address Line2"), max_length=254)
    reg_city = models.CharField(_("Reg. City"), max_length=254)
    reg_state = models.CharField(_("Reg. State"), max_length=254)
    reg_pincode = models.CharField(_("Reg. Pincode"), max_length=254)
    reg_country = models.CharField(_("Reg. Country"), max_length=254)
    corp_address1 = models.CharField(_("Corp. Address Line1"), max_length=254, blank=True, null=True)
    corp_address2 = models.CharField(_("Corp. Address Line2"), max_length=254, blank=True, null=True)
    corp_city = models.CharField(_("Corp. City"), max_length=254, blank=True, null=True)
    corp_state = models.CharField(_("Corp. State"), max_length=254, blank=True, null=True)
    corp_pincode = models.CharField(_("Corp. Pincode"), max_length=254, blank=True, null=True)
    corp_country = models.CharField(_("Corp. Country"), max_length=254, blank=True, null=True)
    branch = models.IntegerField(_("branch id"), blank=True, null=True)
    inserted_at = models.DateTimeField(_("Inserted"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited"), blank=True, null=True)
    inserted_by = models.IntegerField(_("Inserted By"))

    class Meta:
        verbose_name = _("Biller")
        verbose_name_plural = _("Billers")
        db_table = "Biller"
        constraints = [
            models.UniqueConstraint(
                fields=['biller_name', 'biller_gstin', 'branch'],
                name='unique_biller_name_gstin_branch'
            )
        ]

    def get_reg_full_address(self):
        address_parts = [
            self.reg_address1,
            self.reg_address2,
            self.reg_city,
            self.reg_pincode,
            self.reg_state,
            self.reg_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def get_corp_full_address(self):
        address_parts = [
            self.corp_address1,
            self.corp_address2,
            self.corp_city,
            self.corp_pincode,
            self.corp_state,
            self.corp_country
        ]
        return ', '.join(filter(None, address_parts))
    
    def __str__(self):
        return f'{self.biller_name} - {self.reg_state}'
    
    

class BillerVariable(models.Model):
    biller_id = models.ForeignKey(Biller, verbose_name=_("Biller Id"), on_delete=models.CASCADE, related_name="variables")
    variable_name = models.CharField(_("Variable Name"), max_length=50, choices=VARIABLES)
    variable_value = models.CharField(_("Variable Value"), max_length=150)
    from_date = models.DateField(_("From Date"), null=False, blank=False)
    to_date = models.DateField(_("To Date"), null=True, blank=True)
    inserted_by = models.IntegerField(_("Inserted By"))
    Inserted_at = models.DateTimeField(_("Inserted At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Biller Variable")
        verbose_name_plural = _("Biller Variables")
        db_table = "Biller_Variable"

    def __str__(self):
        return f'{self.id} - {self.biller_id.biller_name} - {self.variable_name}: {self.variable_value}'
    


class BankDetail(models.Model):

    biller = models.ForeignKey(Biller, on_delete=models.SET_NULL, null=True, related_name='banks')
    is_active = models.BooleanField(_("Is Active"), default=True)
    is_upi = models.BooleanField(_("Is UPI"), default=False)
    upi_id = models.CharField(_("UPI ID"), max_length=50, blank=True, null=True)
    upi_no = models.CharField(_("UPI No"), max_length=50, blank=True, null=True)
    bnf_name = models.CharField(_("Beneficiary Name"), max_length=150, blank=False, null=False)
    bank_name = models.CharField(_("Bank Name"), max_length=150, blank=True, null=True)
    branch_address = models.CharField(_("Branch Address"), max_length=254, blank=True, null=True)
    ac_no = models.CharField(_("A/c No"), max_length=150, blank=True, null=True)
    ifsc = models.CharField(_("IFSC"), max_length=50, blank=True, null=True)
    swift_code = models.CharField(_("Swift Code"), max_length=50, blank=True, null=True)
    inserted_at = models.DateTimeField(_("Inserted at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)
    inserted_by = models.IntegerField(_("Inserted By"))
    branch = models.IntegerField(_("branch"), blank=True, null=True)

    upi_qr = models.ImageField(_("upi qr"), upload_to=f"upi_qr_code/", blank=True, null=True)

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        db_table = "Bank_List"
        constraints = [
            models.UniqueConstraint(
                fields=['bnf_name', 'bank_name', 'ac_no', 'upi_id', 'upi_no', 'branch'],
                name="unique_bnf_bank_ac_upi_id_no_branch"
            )
        ]

    def __str__(self):
        return f'{self.bank_name} - {self.bnf_name}'
    
    def get_upi_uri(self):
        if not self.upi_id:
            return None
        return f"upi://pay?pa={self.upi_id}&pn={self.bnf_name}&cu=INR"