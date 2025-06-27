from django.utils.translation import gettext_lazy as _

ROLE_CHOICES = (
        ('admin',_('Admin')),
        ('sub-admin', _('Sub-admin')),
        ('user',_('User')),
        )


DEPARTMENTS = (
    ('account',_('Account')),
    ('production',_('Production')),
    ('sales', _('Sales'))
)

VARIABLES = (
    ('position', _('Position')),
    ('sales_target', _('Sales Target')),
)

POSITIONS = (
    ('head', _('HEAD')),
    ('vp', _('VP')),
    ('sr. manager', _('SR. MANAGER')),
    ('member', _('MEMBER'))
)