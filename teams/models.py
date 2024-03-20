from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _
from .managers import UserManager

class User(AbstractUser):

    ROLE = (('admin','Admin'), ('user','User'))
    DEPARTMENT = (('account','Account'),('production','Production'), ('sales', 'Sales'))

    username = None
    first_name = models.CharField(max_length=155, blank=True, default = 'guest')
    last_name = models.CharField(max_length=155, blank=True, default = 'user')
    email = models.EmailField(max_length=254, unique=True, blank = False)
    role = models.CharField(max_length=100, choices=ROLE, default="user")
    department = models.CharField(max_length=100, choices=DEPARTMENT, default="sales")
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
        return f'{self.branch_name} {self.city}'
    
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
