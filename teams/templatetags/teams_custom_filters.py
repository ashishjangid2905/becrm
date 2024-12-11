from django import template
from datetime import datetime
from django.db.models import Q
from teams.models import UserVariable

register = template.Library()


@register.simple_tag
def get_current_target(user_profile):
    today = datetime.now().date()

    filters = {'from_date__lte': today, 'user_profile': user_profile, 'variable_name': 'sales_target' }

    variable = UserVariable.objects.filter(
        Q(to_date__gte=today) | Q(to_date__isnull = True),
        **filters).last()

    return variable.variable_value if variable else None