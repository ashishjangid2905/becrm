from django.db.models.signals import post_save, post_delete
from django.db.models import Q
from django.contrib.auth.models import Group
from django.dispatch import receiver
from teams.models import Profile, UserVariable
from datetime import datetime


@receiver(post_save, sender=UserVariable)
def assign_group_based_on_position(sender, instance, **kwargs):
    today = datetime.now().date()

    # Ensure we are passing a Profile instance here (instance.user_profile is correct)
    if isinstance(instance.user_profile, Profile):  # Make sure it's a Profile instance
        filters = {
            'from_date__lte': today,
            'user_profile': instance.user_profile,  # Correct reference to Profile instance
            'variable_name': 'position',
        }

        position_profile = UserVariable.objects.filter(
            Q(to_date__gte=today) | Q(to_date__isnull=True),
            **filters
        ).last()

        if position_profile:
            position = position_profile.variable_value
            group, created = Group.objects.get_or_create(name=position)

            # Clear existing groups and assign the new group
            instance.user_profile.user.groups.clear()
            instance.user_profile.user.groups.add(group)

@receiver(post_delete, sender=UserVariable)
def handle_user_variable_delete(sender, instance, **kwargs):
    if isinstance(instance.user_profile, Profile):  # Check if it's a Profile instance
        today = datetime.now().date()
        filters = {
            'from_date__lte': today,
            'user_profile': instance.user_profile,
            'variable_name': 'position',
        }
        position_profile = UserVariable.objects.filter(
            Q(to_date__gte=today) | Q(to_date__isnull=True),
            **filters
        ).last()

        if position_profile:
            position = position_profile.variable_value
            group, created = Group.objects.get_or_create(name=position)

            # Clear existing groups and assign the new group
            instance.user_profile.user.groups.clear()
            instance.user_profile.user.groups.add(group)
