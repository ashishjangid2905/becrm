from django.db import models
import os
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _
from .managers import UserManager
from django.utils import timezone
from .utils import ROLE_CHOICES, DEPARTMENTS, VARIABLES
from cryptography.fernet import Fernet

class User(AbstractUser):

    ROLE = (('admin','Admin'), ('user','User'))
    DEPARTMENT = (('account','Account'),('production','Production'), ('sales', 'Sales'))

    username = None
    first_name = models.CharField(max_length=155, blank=True, default = 'guest')
    last_name = models.CharField(max_length=155, blank=True, default = 'user')
    email = models.EmailField(max_length=254, unique=True, blank = False)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default="user")
    department = models.CharField(max_length=100, choices=DEPARTMENTS, default="sales")
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    

class Branch(models.Model):

    branch_name = models.CharField(max_length=155, blank=False)
    address = models.CharField(max_length = 255, blank = True, default ="")
    street = models.CharField(max_length = 255, blank = True, default ="")
    city = models.CharField(max_length = 255, blank = True, default ="")
    state = models.CharField(max_length = 255, blank = True, default ="")
    postcode = models.CharField(max_length = 64, blank = True, default ="")
    country = models.CharField(max_length = 255, blank = True, default ="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f'{self.branch_name}, {self.city}'
    
    def full_address(self):
        address_components = [self.address, self.street, self.city, self.state, self.postcode,self.country]
        return ', '. join(filter(None, address_components))
    
def user_profile_path(instance, filename): 
  
    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename> 
    return 'profile/user_{0}/{1}'.format(instance.user.id, filename)
    
class Profile(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dob = models.DateField(_("Date of Birth"), auto_now=False, blank = True, null = True)
    phone = models.CharField(max_length = 50, blank=True, default="")
    profile_img = models.ImageField(_("Profile"), upload_to=user_profile_path, blank=True, default='profile/user-default-96.png')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null = True)
    last_edited = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return str(self.user)
    

class UserVariable(models.Model):

    user_profile = models.ForeignKey(Profile, verbose_name=_("User"), on_delete=models.CASCADE)
    variable_name = models.CharField(_("Variable Name"), max_length=50, choices=VARIABLES)
    variable_value = models.CharField(_("Variable Value"), max_length=250)
    from_date = models.DateField(_("From Date"), default=timezone.now, blank=False, null=False)
    to_date = models.DateField(_("To Date"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created_at"), auto_now_add=True)

    class Meta:
        verbose_name = 'UserVariable'
        verbose_name_plural = 'UserVariables'
        ordering = ['-from_date']
        db_table = "UserVariable"

    def __str__(self):
        return f'{self.user_profile.user.first_name} - {self.variable_name}: {self.variable_value}'
    

class SmtpConfig(models.Model):

    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    smtp_server = models.CharField(_("SMTP Host"), max_length=255, help_text="SMTP server address")
    smtp_port = models.PositiveIntegerField(_("SMTP Port"), help_text="SMTP server port")
    email_host_password = models.CharField(_("Password"), max_length=50)
    use_tls = models.BooleanField(_("Use TLS"), default=True)
    use_ssl = models.BooleanField(_("Use SSL"), default=False)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    def __str__(self):
        return f'{self.smtp_server} ({self.user.email})'
        

    class Meta:
        verbose_name = "SMTP Configuration"
        verbose_name_plural = "SMTP Configurations"
        db_table = "SmtpConfig"
    



    
