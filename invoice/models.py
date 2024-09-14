from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from lead.models import contactPerson, leads
from teams.models import Profile
import fiscalyear, datetime

# Create your models here.

class biller(models.Model):
    biller_name = models.CharField(_("Biller Name"), max_length=150)
    brand_name = models.CharField(_("Brand Name"), max_length=150, null=True, blank=True)
    biller_gstin = models.CharField(_("Biller Gstin"), max_length=150, blank=True, null=True)
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
    inserted_at = models.DateTimeField(_("Inserted"), auto_now=True)
    edited_at = models.DateTimeField(_("Edited"), auto_now_add=True)

    class Meta:
        verbose_name = _("Biller")
        verbose_name_plural = _("Billers")
        db_table = "Biller"
        unique_together = ('biller_name', 'biller_gstin')

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

class bankDetail(models.Model):

    biller_id = models.ForeignKey(biller, on_delete=models.SET_NULL, null=True)
    bnf_name = models.CharField(_("Beneficiary Name"), max_length=150, blank=False, null=False)
    bank_name = models.CharField(_("Bank Name"), max_length=150, blank=False, null=False)
    branch_address = models.CharField(_("Branch Address"), max_length=254, blank=True, null=True)
    ac_no = models.CharField(_("A/c No"), max_length=150, blank=False, null=False)
    ifsc = models.CharField(_("IFSC"), max_length=50, blank=False, null=False)
    swift_code = models.CharField(_("Swift Code"), max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")
        db_table = "Bank_List"
        unique_together = ('bnf_name', 'bank_name', 'ac_no')

    def __str__(self):
        return self.bank_name

def pi_number(user):
    fiscalyear.START_MONTH = 4
    fy = str(fiscalyear.FiscalYear.current())[-2:]
    py = str(int(fy) - 1)


    branch_id = Profile.objects.get(user=user).branch.id

    prefix = 'BE' if branch_id == 1 else 'CE'

    n = proforma.objects.filter(pi_no__startswith=f"{py}-{fy}/{prefix}-").order_by('pi_no').last()


    if n:
        last_no = int(n.pi_no.split('-')[-1])
        new_no = last_no + 1
    else:
        new_no = 1

    return f"{py}-{fy}/{prefix}-{str(new_no).zfill(4)}"


class proforma(models.Model):
    
    company_ref = models.ForeignKey(leads, verbose_name=_("Company Ref"), on_delete=models.RESTRICT, blank=True, null=True)
    user_id = models.IntegerField(_("User Id"))
    company_name = models.CharField(_("Company Name"), max_length=150, null=False, blank=False)
    gstin = models.CharField(_("GSTIN"), max_length=50, null=True, blank=True)
    is_sez = models.BooleanField(_("Is_SEZ"), default=False)
    lut_no = models.CharField(_("LUT No"), blank=True, null=True, max_length=50)
    vendor_code = models.CharField(_("Vendor Code"), blank=True, null=True, max_length=50)
    address = models.TextField(_("Address"), max_length=1000)
    country = models.CharField(_("Country"), max_length=50)
    state = models.CharField(_("State"), max_length=50)
    requistioner = models.CharField(_("Requistioner"), max_length=50, null=False, blank=False)
    email_id = models.EmailField(_("Email"), max_length=254)
    contact = models.CharField(_("Contact No"), max_length=50)
    pi_no = models.CharField(_("PI No"), max_length=50, default=pi_number, null=False, blank=False, unique=True)
    pi_date = models.DateField(_("PI Date"), auto_now_add=True, null=False)
    po_no = models.CharField(_("PO No"), max_length=50, blank=True, null=True)
    po_date = models.DateField(_("PO Date"), auto_now=False, blank=True, null=True)
    subscription = models.CharField(_("Subscription Mode"), max_length=50)
    payment_term = models.CharField(_("Payment Term"), max_length=50)
    bank = models.ForeignKey(bankDetail, on_delete=models.RESTRICT)
    currency = models.CharField(_("Currency"), max_length=50)
    details = models.TextField(_("Details"), max_length=1000)
    is_Approved = models.BooleanField(_("Is_Approved"), default=False)
    approved_by = models.IntegerField(_("Approved By"), blank=True, null=True)
    approved_at = models.DateTimeField(_("Approved At"), auto_now=True)
    status = models.CharField(_("Status"), max_length=50, default='open')
    closed_at = models.DateField(_("Closing Date"), auto_now=False, auto_now_add=False, null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    edited_by = models.IntegerField(_("Edited By"), blank=True, null=True)
    edited_at = models.DateTimeField(_("Edited At"), auto_now=True)
    slug = models.SlugField(_("slug"), unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.pi_no)
        super().save(*args,**kwargs)

    class Meta:
        verbose_name = _("proforma")
        verbose_name_plural = _("proformas")
        db_table = "Proforma_Invoice"

    def __str__(self):
        return self.company_name

class orderList(models.Model):
    
    proforma_id = models.ForeignKey(proforma, on_delete=models.RESTRICT)
    category = models.CharField(_("Category"), max_length=50, blank=False, null=False)
    report_type = models.CharField(_("Report Type"), max_length=50)
    product = models.CharField(_("Product"), max_length=50)
    from_month = models.CharField(_("From Month"), max_length=50)
    to_month = models.CharField(_("To Month"), max_length=50)
    unit_price = models.IntegerField(_("Unit Price"), blank=True, null=True)
    total_price = models.IntegerField(_("Total Price"), blank=True, null=True)
    lumpsum_amt = models.IntegerField(_("Lumpsum"), blank=True, null=True)
    is_lumpsum = models.BooleanField(_("Is_Lumpsum"), default=False)
    order_status = models.CharField(_("Order Status"), max_length=50, default='pending')
    inserted_at = models.DateTimeField(_("Inserted At"), auto_now=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        db_table = "Order_List"
    
    def __str__(self):
        return self.report_type
    
