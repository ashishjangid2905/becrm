from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
from teams.models import User, Profile
from invoice.utils import STATE_CHOICE, COUNTRY_CHOICE
from .utils import STATUS

class leads(models.Model):

    company_name = models.CharField(_("Company Name"), max_length=150, blank=False, null=False)
    gstin = models.CharField(_("GSTIN"), max_length=16, blank=True, null=True)
    address1 = models.CharField(_("Address Line 1"), max_length=255, blank=False, null=False)
    address2 = models.CharField(_("Address Line 2"), max_length=255, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=False, null=False)
    state = models.CharField(_("State"), max_length=255, blank=False, null=False)
    country = models.CharField(_("Country"), max_length=255, blank=False, null=False)
    pincode = models.CharField(_("Pin Code"), max_length=255, blank=True, null=True)
    industry = models.CharField(_("Industry"), max_length=255, blank=True, null=True)
    full_address = models.CharField(_("full address"), max_length=512, blank=True)
    source = models.CharField(_("Source"), max_length=50, null=False, blank=False, default='email')
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)
    user = models.IntegerField(_("User Id"))
    status = models.CharField(_("Lead Status"), max_length=50, default='new lead', choices=STATUS)
    branch = models.IntegerField(_("branch"), blank=True, null=True)

    @property
    def user_id(self):
        return Profile.objects.get(pk=self.user)
    
    # def get_full_address(self):
    #     state_name = dict(STATE_CHOICE).get(int(self.state), self.state) if self.state != 500 else ""
    #     country = dict(COUNTRY_CHOICE).get(self.country, self.country)

    #     address_parts = [
    #         self.address1,
    #         self.address2,
    #         self.city,
    #         self.pincode,
    #         state_name,
    #         country,
    #     ]
    #     return ', '.join(filter(None, address_parts)).replace(",,",",")

    # def save(self, *args, **kwargs):
    #     self.full_address = self.get_full_address()
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        db_table = "Leads"
        unique_together = ('company_name', 'gstin', 'user')
        indexes = [
            models.Index(fields=['gstin', 'company_name']),
            models.Index(fields=['company_name'], name='company_name_idx')
        ]

    def __str__(self):
        return self.company_name
    

class contactPerson(models.Model):

    person_name = models.CharField(_("Contact Person"), max_length=50, blank=False, null=False)
    email_id = models.CharField(_("Email Id"), max_length=155, blank=True, null=True)
    contact_no = models.CharField(_("Contact No"), max_length=50, blank=True, null=True)
    company = models.ForeignKey(leads, verbose_name=_("Company Id"), on_delete=models.CASCADE, related_name=_("contactpersons"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    branch = models.IntegerField(_("branch"), blank=True, null=True)

    def toggle_active(self):
        self.is_active = not self.is_active
        self.save()

    class Meta:
        verbose_name = 'Contact Person'
        verbose_name_plural = 'Contact Persons'
        db_table = "ContactPersons"

    def __str__(self):
        return self.person_name
    
   
class Conversation(models.Model):

    title = models.CharField(_("Tittle"), max_length=250)
    company_id = models.ForeignKey(leads, verbose_name=_("Company Id"), on_delete=models.CASCADE)
    start_at = models.DateTimeField(_("Started at"), auto_now_add=True)
    branch = models.IntegerField(_("branch"), blank=True, null=True)

    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        db_table = "Conversations"

    def __str__(self):
        return self.title
    

class conversationDetails(models.Model):
    STATUS = (('open', 'Open'), ('closed', 'Closed'), ('lost', 'Lost'))

    details = models.TextField(_("Details"))
    contact_person = models.ForeignKey(contactPerson, verbose_name=_("Contact Person"), on_delete=models.CASCADE)
    status = models.CharField(_("Status"), max_length=50, choices=STATUS, default='open')
    follow_up = models.DateField(_("Next Follow Up"), blank=True, null=True)
    chat_no = models.ForeignKey(Conversation, verbose_name=_("Chat No"), on_delete=models.CASCADE, related_name=_("conversationdetails"))
    inserted_at = models.DateTimeField(_("Inserted at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), auto_now=True)

    class Meta:
        verbose_name = 'Conversation Detail'
        verbose_name_plural = 'Conversation Details'
        db_table = "ConversationDetails"



class InboundLeads(models.Model):

    name = models.CharField(_("name"), max_length=50)
    company_name = models.CharField(_("company name"), max_length=50)
    location = models.CharField(_("location"), max_length=50, blank=True, null=True)
    email = models.EmailField(_("email"), max_length=254)
    contact_no = models.CharField(_("contact no"), max_length=50)
    message = models.TextField(_("message"), max_length=1000)
    source = models.CharField(_("source"), max_length=50)
    assigned_to = models.IntegerField(_("assigned to"), blank=True, null=True)
    assigned_by = models.IntegerField(_("assigned by"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now=False, auto_now_add=True)
    branch = models.IntegerField(_("branch"), blank=True, null=True)

    class Meta:
        verbose_name = "inboundlead"
        verbose_name_plural = "inboundleads"
        db_table = "Inboundleads"

    def __str__(self):
        return f"{self.company_name}: {self.name}"
    
    
    